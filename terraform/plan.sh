#!/bin/bash

# Load environment variables from .env file
export $(grep -v '^#' ../.env | xargs)

# Run Terraform commands
terraform plan \
  -var "AWS_ACCESS_KEY=$AWS_ACCESS_KEY" \
  -var "AWS_SECRET_KEY=$AWS_SECRET_KEY" \
  -var "LEDAA_LOAD_DATA_LAMBDA_LAYER_ARN=$LEDAA_LOAD_DATA_LAMBDA_LAYER_ARN" \
  -var "LEDAA_TEXT_SPLITTER_ARN=$LEDAA_TEXT_SPLITTER_ARN"  \
  -var "GOOGLE_API_KEY=$GOOGLE_API_KEY" \
  -var "PINECONE_API_KEY=$PINECONE_API_KEY" \
  -var "PINECONE_INDEX_HOST=$PINECONE_INDEX_HOST"