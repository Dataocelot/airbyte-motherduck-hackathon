import hashlib
import json
import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Optional

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pyairtable import Api

from helper.logger import Logger

load_dotenv()

logger_instance = Logger()
logger = logger_instance.get_logger()

TOC_IMAGE_PROMPT = """
            This {file_type} depicts the table of contents from a user manual for a {device}.
            **Task:**

            Extract the section and subsection names, along with their corresponding page numbers, from the file.
            Make sure the returned section names are in snakecase and all lowercase.

            **Output Format:**

            Provide the results as a {dest_file_type} object with the following structure:

            ```json
            {expected_output}
            ```
            """

JSON_PG_NUM_PROMPT = """This a table of contents {file_type} file for a {device} user manual
            **Task:**

            Extract the relevant subsections you think that might help find details regarding {subject_of_interest} of this {device} from the file.
            Make sure the returned subsection names are in snakecase and all lowercase.

            **Output Format:**

            Provide the results as a {dest_file_type} object with the following structure:

            ```json
            {expected_output}
            ```
            """


def auto_create_dir(directory: str | Path) -> None:
    """
    Check if a directory exists, and if not, create it

    Parameters
    ----------
    directory : str
        The directory to check if it exists
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
    except Exception as e:
        logger.error(f"Error creating directory: {e}")
        raise e


def get_hash_from_file(file_path: str) -> str:
    """
    Get the hash of a file

    Parameters
    ----------
    file_path : str
        The path to the file to get the hash of

    Returns
    -------
    str
        The hash of the file
    """
    try:
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5(usedforsecurity=False)
            while chunk := f.read(8192):
                file_hash.update(chunk)
        return file_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error getting hash from file: {e}")
        raise e


# Save the dictionary to a JSON file
def save_dict_to_json(data, file_path):
    try:
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully saved to {file_path}")
    except Exception as e:
        print(f"Error saving data to JSON: {e}")


def check_file_hash(file_path: str, hash_value: str) -> bool:
    """
    Check if the hash of a file matches a given hash value

    Parameters
    ----------
    file_path : str
        The path to the file to check the hash of
    hash_value : str
        The hash value to check against

    Returns
    -------
    bool
        True if the hash values match, False otherwise
    """
    file_hash = get_hash_from_file(file_path)
    return file_hash == hash_value


class ScraperOption(Enum):
    SELENIUM = "selenium"
    REQUESTS = "requests"


class SourceTypeOption(Enum):
    IMAGE = "img"
    PDF = "pdf"
    JSON = "json"


class ExtractorOption(Enum):
    GEMINI = "gemini"
    TESSERACT = "tesseract"
    PYMUPDF = "pymupdf"


class Environment(Enum):
    LOCAL = "local"
    AWS = "aws"


class ContentType(Enum):
    JPEG = "image/jpeg"
    JPG = "image/jpeg"
    PNG = "image/png"
    WEBP = "image/webp"
    GIF = "image/gif"
    SVG = "image/svg+xml"

    TEXT = "text/plain"
    HTML = "text/html"
    CSS = "text/css"
    JAVASCRIPT = "application/javascript"

    PDF = "application/pdf"
    JSON = "application/json"
    XML = "application/xml"
    CSV = "text/csv"

    OCTET_STREAM = "application/octet-stream"


class PageContentSearchType(Enum):
    CONSECUTIVE_PAGES = "consecutive_pages"
    EARLIEST_PAGE_FIRST = "earliest_page_first"


def get_s3_client(bucket_name: str | None) -> Optional["S3Client"]:
    """Retrieves an S3 client.

    Args:
        bucket_name (str, optional): The name of the S3 bucket.

    Returns:
        S3Client | None: An S3 client object if successful, None otherwise.
        Raises ValueError if bucket_name is None or empty
    """
    if not bucket_name:
        logger.error("Bucket name cannot be empty.")
        raise ValueError("Bucket name is required.")

    try:
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        if aws_access_key_id and aws_secret_access_key:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
        else:
            s3_client = boto3.client("s3")
        return s3_client
    except ClientError as e:
        logger.error(f"AWS ClientError: {e}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred during S3 client creation. {e}")
        return None


def save_file_to_s3(
    data: bytes | str | BinaryIO,
    object_key: str | Path,
    content_type: str | None = None,
    bucket_name: str | None = os.getenv("BUCKET_NAME"),
) -> bool:
    """Saves data to an S3 bucket.

    Parameters:
        data (bytes, str, or BinaryIO): The data to save. Can be bytes (for images, etc.), a string, or a file-like object.
        object_key (str): The key (filename/path) for the object in S3. Can include folders (e.g., "my_folder/my_file.json").
        content_type (str, optional): The content type to save as. If None, S3 will attempt to determine it automatically (less reliable).
        bucket_name (str, optional): The name of the S3 bucket. Defaults to the value of the `BUCKET_NAME` environment variable if not provided.

    Returns:
        bool: True if the data was successfully saved, False otherwise.
    Raises:
        ValueError: If the bucket name is not provided or is empty.
    """
    if not bucket_name:
        logger.error("Bucket name cannot be empty.")
        raise ValueError("Bucket name is required.")

    try:
        s3_client = get_s3_client(bucket_name)
        if s3_client is None:
            logger.error("Failed to create S3 client.")
            return False

        try:
            if content_type:
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=str(object_key),
                    Body=data,
                    ContentType=content_type,
                )
            else:
                s3_client.put_object(Bucket=bucket_name, Key=str(object_key), Body=data)
            logger.info(f"File saved to s3://{bucket_name}/{object_key}")
            return True
        except ClientError as e:
            logger.error(f"AWS ClientError: {e} bucket_name:{bucket_name}")
            return False
    except ValueError as e:
        logger.error(f"Invalid input: {e} bucket_name:{bucket_name}")
        return False
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return False


def get_object_from_s3(
    object_key: str,
    bucket_name: str | None = os.getenv("BUCKET_NAME"),
) -> str | None:
    """Retrieves an object from an S3 bucket and saves it to a temporary file.

    Parameters:
        object_key (str): The key (filename/path) of the object in S3.
        bucket_name (str, optional): The name of the S3 bucket. Defaults to the value of the BUCKET_NAME environment variable if not provided.

    Returns:
        str | None: The path to the temporary file containing the object's content, or None if an error occurs.
    Raises:
        ValueError: if the bucket name is not provided
    """

    if not bucket_name:
        logger.error("Bucket name cannot be empty.")
        raise ValueError("Bucket name is required.")

    try:
        s3_client = get_s3_client(bucket_name)
        if s3_client is None:
            logger.error("Failed to create S3 client.")
            return None

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            temp_file_path = tmp_file.name
            logger.info(
                f"Object key {object_key}",
            )
            s3_client.download_file(bucket_name, str(object_key), temp_file_path)
            logger.info(
                f"File s3://{bucket_name}/{object_key} saved to {temp_file_path}"
            )
            return temp_file_path

    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            logger.error(f"Object '{object_key}' not found in bucket '{bucket_name}'.")
        else:
            logger.error(f"AWS ClientError: {e}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return None


def get_airtable_table(
    table_id: str,
    base_id: str | None = None,
):
    """
    Retrieve an Airtable table using the provided table ID and base ID.

    Args:
        table_id (str): The ID of the Airtable table to retrieve.
        base_id (str): The ID of the Airtable base. Defaults to the value of the environment variable "AIRTABLE_BASE_ID".

    Returns:
        table: The Airtable table object if retrieval is successful, otherwise None.

    Raises:
        Exception: If there is an error during the retrieval process, the exception is caught and printed.
    """

    table = None
    if not base_id:
        base_id = os.environ["AIRTABLE_BASE_ID"]
    try:
        api = Api(os.environ["AIRTABLE_API_KEY"])
        table = api.table(base_id, table_id)
    except Exception as e:
        print(e)
    return table
