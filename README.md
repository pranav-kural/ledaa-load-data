# LEDAA Load Data

LEDAA project is about building a conversational AI assistant for [FRAGMENT (documentation)](https://fragment.dev/docs). Towards this purpose, the **LEDAA Load Data** project is mainly intended to handle the overall ingestion of data when new changes in the ground truth (i.e., documentation webpages) are observed. The project is part of the larger LEDAA project and is responsible for processing and storing document chunks in the knowledge base vector store.

To learn more check: [Building AI Assistant for FRAGMENT documentation](https://www.pkural.ca/blog/posts/fragment/)

![ledaa-load-data](https://github.com/user-attachments/assets/029cd02e-62ee-4da7-8a4a-0fa0394665c3)

## Process Flow

Below is the process flow for how ground truth data updates are handled and how the knowledge base is effectively updated.

1. [`ledaa_updates_scanner`](https://github.com/pranav-kural/ledaa-updates-scanner) Lambda function monitors for changes in content of documentation.
2. On detecting changes, it triggers the [`ledaa_load_data`](https://github.com/pranav-kural/ledaa-load-data) Lambda function passing it the URL of webpage.
3. `ledaa_load_data` Lambda function invokes the [`ledaa_text_splitter`](https://github.com/pranav-kural/ledaa-text-splitter) Lambda function to initiate the process of scraping data from a given URL and to get a list of strings (representing text chunks or documents) which will be used in data ingestion.
4. `ledaa_text_splitter` Lambda function invokes the [`ledaa_web_scrapper`](https://github.com/pranav-kural/ledaa-web-scrapper) Lambda function to scrape the URL and store the processed markdown data in S3. `ledaa_web_scrapper` function also stores the hash of the processed data in DynamoDB which will later be compared by `ledaa_updates_scanner` function to detect changes.
5. On receiving processed document chunks back, `ledaa_load_data` Lambda function stores the data in the vector store.

## Core Functionality

The `core.py` file contains the main logic for processing and storing document chunks in a vector store. It leverages AWS Lambda, Pinecone, and Google Generative AI for various tasks. Below is a summary of the key functions and their purposes:

1. **Constants and Singleton Instances**:

    - `EMBEDDING_MODEL`: The model used for generating embeddings.
    - `vector_store_idx`: A singleton instance of the Pinecone index.

2. **Functions**:
    - `get_vector_store_index()`: Initializes and returns the Pinecone index instance.
    - `delete_existing_chunks(url)`: Deletes existing chunks in the vector store for a given URL.
    - `get_embeddings(text)`: Generates embeddings for the given text using the specified embedding model.
    - `prepare_data_for_upsert(url, data_chunks)`: Prepares data chunks for upsert operation in the vector store.
    - `store_chunks_in_vector_store(url, data_chunks)`: Stores the document chunks in the vector store.
    - `get_data_chunks(url)`: Invokes the `ledaa_text_splitter` Lambda function to preprocess data and get document chunks.
    - `main(url)`: Main function that orchestrates the entire process of deleting existing chunks, getting data chunks, and storing them in the vector store.
    - `lambda_handler(event, context)`: AWS Lambda handler function that invokes the `main` function.

The `core.py` file is designed to be invoked by the `ledaa_updates_scanner` Lambda function, and the `lambda_handler` function serves as the entry point for the Lambda function. The main process involves deleting existing chunks for a given URL, retrieving new data chunks by invoking another Lambda function, generating embeddings for the chunks, and storing them in the Pinecone vector store.

## AWS Lambda Deployment

We deploy the scanner function to AWS Lambda using [Terraform](https://www.terraform.io/). The Terraform configuration files can be found in the `terraform` directory. The configuration file creates:

-   Appropriate AWS role and policy for the Lambda function.
-   AWS Lambda Layer for the Lambda function using pre-built compressed lambda layer zip file (present in `terraform/packages`, created using `create_lambda_layer.sh`).
-   Data archive file for the core code (`core.py`).
-   AWS Lambda function using the data archive file, the Lambda Layer, and the appropriate role.

There are certain scripts in `terraform` directory, like `apply.sh` and `plan.sh`, which can be used to apply and plan the Terraform configuration respectively. These scripts extract necessary environment variables from the `.env` file and pass them to Terraform.

## LICENSE

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
