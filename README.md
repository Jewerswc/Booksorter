# Booksorter

A Python command-line tool that helps you decide whether to **KEEP** or **CHUCK** a book based on whether you are likely to read it someday. The tool uses the [Open Library API](https://openlibrary.org/developers/api) to fetch metadata (title, authors, and subjects) for a given ISBN and compares the new book's topics against a list of books you have already read.

## Features

- **Fetch Metadata:** Retrieves book details (title, authors, subjects) using the Open Library API.
- **Subject Splitting:** Automatically splits subject strings (e.g., `"world war, cryptography"`) into individual tokens for more accurate comparison.
- **Similarity Comparison:** Uses a Jaccard similarity measure to compare the subjects of a new book with those from your read books.
- **Decision Making:** 
  - **KEEP:** If an author match is found or if the subject similarity exceeds a defined threshold.
  - **CHUCK:** If neither an author match nor sufficient subject similarity is found.
- **Interactive CLI:** Easily input new ISBNs and get an immediate decision with an explanation.

## Requirements

- Python 3.6+
- [Requests](https://pypi.org/project/requests/)

You can install the required package using:

```bash
pip install requests
