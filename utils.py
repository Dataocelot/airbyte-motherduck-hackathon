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


class ExtractorOption(Enum):
    GEMINI = "gemini"
    TESSERACT = "tesseract"
    PYMUPDF = "pymupdf"


TOC_IMAGE_PROMPT = """
                    This is a table of contents image in a user manual for a {device}. Give me a Json of all sections and subsections with their page numbers.
                    The result should be a key value pair with the section/subsection name as the key and page number as the value.
                    The section names should all be in snakecase
                    Make the section names all nakecase, page_numbers an integer, and make all section names lowercase, remove any encoding.

                    Example:
                    {
                        "introduction": 1,
                        "installation_of_parts": 3,
                        "usage": 5,
                        "maintenance": 7,
                        "troubleshooting": 9,
                    }
                    “"""

TROUBLESHOOTING_PROMPT = """This a table of contents image in a user manual, I want you to extract the relevant sections and page numbers (key, value) in JSON that you think will be related to troubleshooting section from this image.
                            The result should be a list of section names that you think are related to parts of the dishwasher.
                            Make sure the section names are in snakecase and all lowercase."""

PARTS_PROMPT = """This a table of contents image in a {device} user manual, I want you to extract the relevant sections you think that are related to where I might be able to find an image of parts for the Dishwasher.
                    The result should be a list of section names that you think are related to parts of the dishwasher.
                    Make the page_number an integer, and make all section names lowercase, remove any encoding.

                    Make sure the section names are in snakecase and all lowercase."""
