import fitz  # PyMuPDF for PDF text extraction
import camelot  # For table extraction from PDF
from transformers import pipeline  # For text summarization (optional)

# A function to extract text from PDF using PyMuPDF
def extract_pdf_text(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

# A function to extract tables from PDF using Camelot
def extract_pdf_tables(pdf_path):
    tables = []
    try:
        # First attempt with 'stream' flavor
        extracted_tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
        if not extracted_tables:
            # If no tables detected, try the 'lattice' flavor
            extracted_tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")
        
        if extracted_tables:
            # Log how many tables were detected
            print(f"Detected {len(extracted_tables)} tables")
            for table in extracted_tables:
                tables.append(table.df.to_json())  # Convert table to JSON
        else:
            print("No tables detected with both 'stream' and 'lattice' methods.")
    except Exception as e:
        print(f"Error extracting tables from PDF: {e}")
    return tables

# A function to summarize text (using Hugging Face pipeline or simple approach)
def summarize_text(text):
    try:
        # Option 1: Using Hugging Face's summarization model
        summarizer = pipeline("summarization")
        summary = summarizer(text, max_length=150, min_length=30, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Error summarizing text: {e}")
        # Fallback: Return first 500 characters as a simple summary
        return text[:500]

# A function to split large tables into smaller parts
def split_large_tables(tables, max_rows=50):
    """Split tables into smaller parts if they exceed the max_rows limit."""
    table_chunks = []
    for table in tables:
        table_df = camelot.read_pdf(table)  # Assuming table is a path or object
        if len(table_df) > max_rows:
            # Split into smaller parts
            num_chunks = (len(table_df) // max_rows) + 1
            for i in range(num_chunks):
                chunk = table_df[i * max_rows:(i + 1) * max_rows]
                table_chunks.append(chunk)
        else:
            table_chunks.append(table_df)
    return table_chunks
