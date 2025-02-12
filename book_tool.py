import requests
import sys
import time

# Global cache for author names (to avoid repeated API calls)
author_cache = {}

def load_read_books(filename="read_books.txt"):
    """
    Loads the list of ISBNs of books you have read.
    The file should have one ISBN per line.
    Returns a set of ISBN strings.
    """
    try:
        with open(filename, "r") as file:
            return {line.strip() for line in file if line.strip()}
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found. Please create the file with one ISBN per line.")
        sys.exit(1)

def get_book_info(isbn):
    """
    Uses the Open Library API to fetch book information for the given ISBN.
    Returns a dictionary with the book data or None if the request fails.
    """
    url = f"https://openlibrary.org/isbn/{isbn}.json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Warning: Could not retrieve info for ISBN {isbn} (status code {response.status_code}).")
            return None
    except Exception as e:
        print(f"Error retrieving book info for ISBN {isbn}: {e}")
        return None

def get_author_name(author_key):
    """
    Given an author key (e.g., "/authors/OL2162285A"), fetch the author name from Open Library.
    Caches results to minimize API calls.
    """
    global author_cache
    if author_key in author_cache:
        return author_cache[author_key]
    
    url = f"https://openlibrary.org{author_key}.json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            name = data.get("name")
            author_cache[author_key] = name
            # To be polite with the API, wait a bit between requests.
            time.sleep(0.1)
            return name
        else:
            return None
    except Exception as e:
        return None

def get_book_features(isbn):
    """
    For a given ISBN, fetch its Open Library metadata and extract features:
      - title
      - subjects (as a set of lowercase individual topics)
      - authors (as a set of lowercase strings)
    Returns a dictionary with these features.
    """
    info = get_book_info(isbn)
    if not info:
        return None

    features = {}
    features['title'] = info.get('title', 'Unknown Title')

    # Extract subjects, splitting comma-separated values into individual tokens
    subjects = set()
    if 'subjects' in info and isinstance(info['subjects'], list):
        for subject in info['subjects']:
            if isinstance(subject, str):
                # Split the subject string on commas and add each token
                for part in subject.lower().split(','):
                    token = part.strip()
                    if token:
                        subjects.add(token)
            elif isinstance(subject, dict):
                # In some cases, subject may be a dict with a 'name' field.
                name = subject.get('name')
                if name:
                    for part in name.lower().split(','):
                        token = part.strip()
                        if token:
                            subjects.add(token)
    features['subjects'] = subjects

    # Extract authors (unchanged)
    authors = set()
    if 'authors' in info and isinstance(info['authors'], list):
        for author in info['authors']:
            if isinstance(author, dict):
                # Sometimes the API returns a 'name' directly.
                if 'name' in author:
                    authors.add(author['name'].lower())
                elif 'key' in author:
                    author_name = get_author_name(author['key'])
                    if author_name:
                        authors.add(author_name.lower())
    features['authors'] = authors

    return features

def jaccard_similarity(set1, set2):
    """
    Computes the Jaccard similarity between two sets.
    Returns a float between 0 and 1.
    """
    if not set1 and not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)

def decide_based_on_features(new_features, read_features_list, subject_threshold=0.2):
    """
    Given the features of a new book and a list of features from read books,
    decide whether to KEEP (likely to be read someday) or CHUCK it.
    
    Criteria:
      - If the new book shares any author with a read book, immediately KEEP.
      - Otherwise, compute the Jaccard similarity for subjects between the new book and each read book.
        If the maximum similarity exceeds the subject_threshold, KEEP; else, CHUCK.
    Returns a tuple (decision_str, explanation).
    """
    # Check for author match first
    new_authors = new_features.get('authors', set())
    for features in read_features_list:
        if features.get('authors', set()).intersection(new_authors):
            matched_authors = features.get('authors').intersection(new_authors)
            return ("KEEP", f"Author match found ({', '.join(matched_authors)})")
    
    # Debug: Print subjects for the new book
    new_subjects = new_features.get('subjects', set())
    print("New book subjects:", new_subjects)
    
    # No author match; now check subject similarity
    max_similarity = 0.0
    best_match_title = None
    for features in read_features_list:
        read_subjects = features.get('subjects', set())
        print(f"Comparing with '{features.get('title', 'Unknown Title')}' subjects: {read_subjects}")
        similarity = jaccard_similarity(new_subjects, read_subjects)
        print(f"Similarity: {similarity:.2f}")
        if similarity > max_similarity:
            max_similarity = similarity
            best_match_title = features.get('title', 'Unknown Title')
    
    if max_similarity >= subject_threshold:
        return ("KEEP", f"Subject similarity {max_similarity:.2f} (best match: '{best_match_title}')")
    else:
        return ("CHUCK", f"Maximum subject similarity {max_similarity:.2f} is below threshold {subject_threshold}")
    
def load_read_books_features(read_books):
    """
    Given a set of read book ISBNs, fetch and return their features in a list.
    """
    features_list = []
    print("Fetching features for read books...")
    for isbn in read_books:
        features = get_book_features(isbn)
        if features:
            features_list.append(features)
        else:
            print(f"Warning: Could not fetch features for ISBN {isbn}.")
    print(f"Loaded features for {len(features_list)} read books.\n")
    return features_list

def main():
    # Load your list of read book ISBNs
    read_books = load_read_books()
    # Preload features for all read books
    read_features_list = load_read_books_features(read_books)

    print("Enter an ISBN to check whether to keep or chuck the book based on your reading history.")
    print("Type 'exit' to quit.")

    while True:
        isbn = input("\nEnter ISBN: ").strip()
        if isbn.lower() == "exit":
            break
        
        new_features = get_book_features(isbn)
        if not new_features:
            print("No metadata found for this ISBN. Defaulting to CHUCK.")
            continue

        # Print basic info about the new book
        print(f"\nBook found: {new_features.get('title', 'Unknown Title')}")
        if new_features.get('authors'):
            print("Authors:", ", ".join(new_features['authors']))
        if new_features.get('subjects'):
            print("Subjects:", ", ".join(new_features['subjects']))

        decision, explanation = decide_based_on_features(new_features, read_features_list)
        print("Decision:", decision)
        print("Explanation:", explanation)

if __name__ == '__main__':
    main()
