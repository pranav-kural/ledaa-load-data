terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.76"
    }
  }

  required_version = ">= 1.5.6"
}

provider "aws" {
  region     = "ca-central-1"
  access_key = var.AWS_ACCESS_KEY
  secret_key = var.AWS_SECRET_KEY
}

resource "aws_iam_role" "lambda_role" {
  name = "ledaa_load_data_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "ledaa_load_data_lambda_policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "lambda:InvokeFunction"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action   = "lambda:InvokeFunction"
        Effect   = "Allow"
        Resource = var.LEDAA_TEXT_SPLITTER_ARN
      }
    ]
  })
}

data "archive_file" "lambda_code" {
  type        = "zip"
  source_file = "../core.py"
  output_path = "packages/ledaa_load_data_package.zip"
}

resource "aws_lambda_function" "ledaa_load_data" {
  function_name = "ledaa_load_data"
  role          = aws_iam_role.lambda_role.arn
  handler       = "core.lambda_handler"
  runtime       = "python3.12"
  architectures = ["x86_64"]

  filename         = "packages/ledaa_load_data_package.zip"
  source_code_hash = data.archive_file.lambda_code.output_base64sha256

  layers = [var.LEDAA_LOAD_DATA_LAMBDA_LAYER_ARN]

  timeout = 60

  environment {
    variables = {
      GOOGLE_API_KEY      = var.GOOGLE_API_KEY
      PINECONE_API_KEY    = var.PINECONE_API_KEY
      PINECONE_INDEX_HOST = var.PINECONE_INDEX_HOST
    }
  }
}