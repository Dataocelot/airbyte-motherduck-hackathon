import hashlib
import json
import os
from enum import Enum
from pathlib import Path

from logger import Logger

logger_instance = Logger()
logger = logger_instance.get_logger()


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


class PageContentSearchType(Enum):
    CONSECUTIVE_PAGES = "consecutive_pages"
    EARLIEST_PAGE_FIRST = "earliest_page_first"


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
