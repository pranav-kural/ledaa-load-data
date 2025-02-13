import os
import uuid
import boto3
import json
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai

# Constants
EMBEDDING_MODEL = 'models/text-embedding-004'

# Singleton instances
vector_store_idx = None

def get_vector_store_index():
    """
    This method returns the Singleton vector store index instance.
    If the instance is not initialized, it initializes the Pinecone index.

    :return: The Pinecone index
    :rtype: Index
    """
    global vector_store_idx
    # Initialize the Pinecone index if not initialized
    if vector_store_idx is None:
        print("Initializing Pinecone index")
        # Validate Pinecone API key
        if "PINECONE_API_KEY" not in os.environ:
            raise Exception("PINECONE_API_KEY environment variable is required")
        # Initialize Pinecone client
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        print("Pinecone client initialized")
        # Instantiate and return Pinecone index
        vector_store_idx = pc.Index(host=os.environ["PINECONE_INDEX_HOST"])
        print("Pinecone index initialized")
    return vector_store_idx

def delete_existing_chunks(url: str):
    """
    This method deletes the existing chunks in the vector store belonging to the URL.
    URL is stored in the metadata of each document chunk on the vector store.

    :param str url: The URL of the page
    """
    print(f"Deleting existing chunks for {url}")
    # Get Singleton vector store index instance
    vector_store_idx = get_vector_store_index()
    # Delete existing chunks in vector store belonging to the URL
    try:
        # Delete chunks in the namespace of the URL
        vector_store_idx.delete(delete_all=True, namespace=url)
    except Exception as e:
        print(f"An error occurred while deleting existing chunks: {e}")
    print(f"Existing chunks deleted for {url}")

def get_embeddings(text: str) -> list[float]:
    """
    This method generates embeddings for the given text using the default embedding model.

    :param str text: The text to generate embeddings for
    :return: The embeddings
    :rtype: list
    """
    # Generate embeddings for the given text
    embedding = genai.embed_content(model=EMBEDDING_MODEL,
                                    content=text,
                                    task_type="retrieval_document")['embedding']
    return embedding

def prepare_data_for_upsert(url: str, data_chunks: list[str]) -> list:
    """
    This method prepares the data chunks for upsert operation in the vector store.
    Creates a multi-dimensional array with each element presenting a record holding values for three columns: `id`, `values`, `metadata`.

    :param str url: The URL of the page
    :param list[str] data_chunks: The document chunks
    :return: The prepared data for upsert operation
    :rtype: list
    """
    print(f"Preparing data for upsert operation for {url}")
    # Prepare data for upsert operation
    data_to_upsert = []
    # Embeddings generation and addition to the list
    # Ideally, when using the 'models/text-embedding-004' model, embeddings of dimension 768 are generated for each chunk
    embeddings = [get_embeddings(text) for text in data_chunks]
    print(f"Embeddings generated for {url}")
    # Add metadata to the DataFrame
    # We add the URL of the page as metadata to each document chunk
    # This enables us to perform filtering based on the URL later on (e.g., to delete existing chunks for a URL)
    metadata = [{'url': url} for _ in range(len(data_chunks))]
    print(f"Metadata added for {url}")
    # Add id field for each chunk (we add at random as we don't need the id field for retrieval or data manipulation)
    # ID is UUID generated for each chunk
    ids = [str(uuid.uuid4()) for _ in range(len(data_chunks))]
    print(f"IDs generated for {url}")
    # Prepare data for upsert operation
    try:
        for i in range(len(data_chunks)):
            data_to_upsert.append([ids[i], embeddings[i], metadata[i]])
            len(data_to_upsert)
    except Exception as e:
        print(f"An error occurred while preparing data for upsert operation: {e}")
    print(f"Data prepared for upsert operation for {url}")
    return data_to_upsert

def store_chunks_in_vector_store(url:str, data_chunks: list[str]):
    """
    This method stores the document chunks in the vector store.
    
    :param str url: The URL of the page (to add to the metadata)
    :param list[str] data_chunks: The document chunks
    """
    print(f"Storing chunks in vector store for {url}")
    try:
        # Prepare data for upsert operation
        data_to_upsert = prepare_data_for_upsert(url=url, data_chunks=data_chunks)
    except Exception as e:
        raise Exception(f"An error occurred while preparing data for upsert operation: {e}")
    # Get Singleton vector store index instance
    vector_store_idx = get_vector_store_index()
    # Store the document chunks in the vector store
    vector_store_idx.upsert(
        namespace=url,
        vectors=[{"id": record[0], "values": record[1], "metadata": record[2]} for record in data_to_upsert]
    )
    print(f"Data stored in vector store for {url}")

def get_data_chunks(url: str) -> list[str]:
    """
    This method invokes the ledaa_text_splitter Lambda function to preprocess the data and get the document chunks.

    :param str url: The URL of the page
    :return: The document chunks
    :rtype: list
    """
    print(f"Invoking LEDAA Text Splitter Lambda for {url}")
    lambda_client = boto3.client('lambda')
    # Invoke the LEDAA Text Splitter Lambda synchronously
    try:
        response = lambda_client.invoke(
            FunctionName='ledaa_text_splitter',
            InvocationType='RequestResponse',
            Payload='{"url": "' + url + '"}'
        )
        # Check invocation status
        if response['StatusCode'] != 200:
            # Log the error
            print(response)
            raise Exception(f"Error: Failed to invoke LEDAA Text Splitter Lambda for {url}")
        else:
            print(f"LEDAA Text Splitter Lambda invoked successfully for {url}")
            # Parse the response
            response_payload = response['Payload'].read().decode('utf-8')
            return json.loads(response_payload)
    except Exception as e:
        raise Exception(f"An error occurred while invoking LEDAA Text Splitter Lambda: {e}")
    
def main(url: str):
    # Validate URL
    if not url:
        return {
            'statusCode': 400,
            'body': 'URL is required'
        }
    try:
        # Delete existing chunks in vector store belonging to the URL
        delete_existing_chunks(url=url)
        # Get data chunks by processing data through LEDAA Text Splitter
        data_chunks = get_data_chunks(url=url)
        if not data_chunks:
            return {
                'statusCode': 500,
                'body': 'Failed to preprocess data'
            }
        print(f"Data chunks retrieved for {url}")
        # Store the document chunks in the vector store
        store_chunks_in_vector_store(url=url, data_chunks=data_chunks)
        # if successful, return success message
        return {    
            'statusCode': 200,
            'body': 'Data stored in vector store'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'An error occurred: {e}'
        }

# Lambda handler method (will be invoked by AWS Lambda)
def lambda_handler(event, context):
    print("LEDAA Load Data Lambda invoked")
    # Validate URL 
    if "url" not in event:
        return {
            'statusCode': 400,
            'body': 'URL is required'
        }
    # Invoke the main method
    return main(url=event["url"])

# Local testing
if __name__ == "__main__":
    print(lambda_handler({"url": ""}, None))