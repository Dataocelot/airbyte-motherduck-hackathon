import hashlib
import os
from enum import Enum

from logger import Logger

logger_instance = Logger()
logger = logger_instance.get_logger()


def auto_create_dir(directory: str) -> None:
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
