import requests
from bs4 import BeautifulSoup
import hashlib
import boto3

import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Constants
BASE_URL = "https://fragment.dev/docs"
HASHES_TABLE = "fragment-docs-hashes"

# Singleton instances
embedding_model = None
vector_store = None

def get_embedding_model():
    """
    This method returns the singleton instance of the embedding model.

    :return SentenceTransformer: The SentenceTransformer instance
    """
    global embedding_model
    if embedding_model is None:
        # Validate the environment variable
        if "GOOGLE_API_KEY" not in os.environ:
            raise Exception("GOOGLE_API_KEY environment variable is required")
        # Initialize the embedding model
        embedding_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    return embedding_model

def main(url: str):
    # Validate URL
    if not url:
        return {
            'statusCode': 400,
            'body': 'URL is required'
        }
    # Delete existing chunks in vector store belonging to the URL
    delete_existing_chunks(url)
    # Get markdown data for the URL from S3
    markdown_data = get_markdown_data(url)
    if not markdown_data:
        return {
            'statusCode': 500,
            'body': 'Failed to fetch markdown data'
        }
    # Pre-process data: text splitting and document chunking
    data_chunks = preprocess_data(markdown_data)
    if not data_chunks:
        return {
            'statusCode': 500,
            'body': 'Failed to preprocess data'
        }
    # Store the document chunks in the vector store
    store_chunks_in_vector_store(url, data_chunks)
    return {    
        'statusCode': 200,
        'body': 'Data stored in vector store'
    }
