"""
Script for cleaning Excel Dataset with QA pairs

This script reads an Excel file containing a dataset, processes the 'content' column by:
- Lowercasing and stripping whitespace
- Replacing emails, links, and phone numbers with placeholders
- Removing extra spaces inside the text

The cleaned text is saved in a new column 'content_clear' and written back to an Excel file.

Dependencies:
- pandas

Usage:
    python clean_dataset.py
"""

import pandas as pd


def clear_spaces_inside(text):
    words = text.split()
    words = [word.strip() for word in words]
    return ' '.join(words)


if __name__ == "__main__":
    PATH_TO_EXCEL = ""
    qa_df = pd.read_excel(PATH_TO_EXCEL)

    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    link_pattern = r'(https?://[^\s]+|www\.[^\s]+)'

    qa_df['content_clear'] = (
        qa_df['content']
        .apply(lambda x: x.lower().strip())
        .str.replace(email_pattern, 'MAIL', regex=True)
        .str.replace(link_pattern, 'LINK', regex=True)
        .str.replace('+7 (xxx) xxx xx xx', 'PHONE', regex=False)
        .apply(clear_spaces_inside)
    )

    qa_df.to_excel(PATH_TO_EXCEL, index=False)
