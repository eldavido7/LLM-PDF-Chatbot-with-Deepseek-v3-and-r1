import os
import fitz  # PyMuPDF for PDF text extraction
import camelot  # For table extraction from PDF
from .api_utils import query_deepseek_r1  # Import our R1 summarizer
import pandas as pd


# A function to extract text from PDF using PyMuPDF
def extract_pdf_text(pdf_path):
    """Memory-efficient PDF text extraction with better error handling"""
    try:
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return None

        doc = fitz.open(pdf_path)
        text_chunks = []

        for page in doc:
            try:
                chunk = page.get_text()
                if chunk:  # Only append non-empty chunks
                    text_chunks.append(chunk)
                page.clean_contents()  # Clean up page resources
            except Exception as page_error:
                print(f"Error extracting text from page: {page_error}")
                continue

        doc.close()  # Explicitly close the document

        if not text_chunks:
            return None

        return "\n".join(text_chunks)

    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None


# A function to extract tables from PDF using Camelot
def extract_pdf_tables(pdf_path):
    """Extract tables from more pages while staying within Render's free tier limits."""
    tables = []
    try:
        max_pages = 20  # Adjusted limit for Render's free tier

        # First check if the PDF exists and is readable
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return tables

        # Get actual page count
        doc = fitz.open(pdf_path)
        actual_pages = min(doc.page_count, max_pages)
        doc.close()

        if actual_pages == 0:
            return tables

        # Use string format for pages only if we have pages to process
        pages_str = f"1-{actual_pages}"
        extracted_tables = camelot.read_pdf(pdf_path, pages=pages_str, flavor="stream")

        if extracted_tables and extracted_tables.n > 0:
            for table in extracted_tables:
                try:
                    if not table.df.empty:
                        # Convert to JSON and clear DataFrame
                        table_json = table.df.to_json(orient="records")
                        tables.append(table_json)
                    del table.df
                except Exception as table_error:
                    print(f"Error processing table: {table_error}")
                    continue

    except Exception as e:
        print(f"Error extracting tables from PDF: {e}")
    return tables


# Updated function to use DeepSeek R1 for summarization
def summarize_text(text, enable_summarization=False):
    """Enable summarization for longer chunks when toggled."""
    if not enable_summarization:
        return text[:2000]  # Adjusted default to larger preview length

    try:
        if len(text) < 2000:
            return text

        # Use DeepSeek R1 for summarization with chunking
        words = text.split()
        chunks = []
        max_chunk_size = 2000

        for i in range(0, len(words), max_chunk_size):
            chunk = " ".join(words[i : i + max_chunk_size])
            prompt = f"Please provide a concise summary of the following text, capturing the main points and key information:\n\n{chunk}"
            summary = query_deepseek_r1(prompt)
            if summary:
                chunks.append(summary)

            if len(chunks) >= 6:  # Allow more chunks
                break

        return " ".join(chunks)
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return text[:2000]


# A function to split large tables into smaller parts
def split_large_tables(tables, max_rows=50):
    """Split tables into smaller parts if they exceed the max_rows limit."""
    table_chunks = []
    for table_json in tables:
        try:
            # Convert JSON string back into a DataFrame
            table_df = pd.read_json(table_json)

            if len(table_df) > max_rows:
                num_chunks = (len(table_df) // max_rows) + 1
                for i in range(num_chunks):
                    chunk = table_df.iloc[i * max_rows : (i + 1) * max_rows]
                    table_chunks.append(chunk.to_json())  # Convert back to JSON
            else:
                table_chunks.append(table_json)  # Keep original JSON if small enough
        except Exception as e:
            print(f"Error processing table: {e}")
    return table_chunks
