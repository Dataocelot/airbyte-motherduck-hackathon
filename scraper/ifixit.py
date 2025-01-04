import datetime

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import Logger, ScraperOption, auto_create_dir

# Initialize logger
logger_instance = Logger()
logger = logger_instance.get_logger()


# Configure ChromeDriver to headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional)
chrome_options.add_argument(
    "--window-size=1920,1080"
)  # Set window size to avoid element location issues

# TODO: Download driver using shell command or package it
# TODO: Add the driver path instead of using ~/.cache/selenium
driver = webdriver.Chrome(options=chrome_options)
WEBSITE_URL = ""


def get_html_content(
    url: str, timeout: int = 20, option: ScraperOption = ScraperOption.REQUESTS
) -> str | None:
    """
    Get the raw HTML from a URL

    Parameters
    ----------
    url : str
        The URL to get the HTML from
    time_out : int (optional)
        The time out to wait for the HTML (default is 20 seconds)
    option : ScraperOption (optional)
        The option to use to get the HTML (default is ScraperOption.REQUESTS)

    Returns
    -------
    str|None
        Raw HTML from the URL or None if an error occurred
    """
    try:
        raw_html = None
        if option == ScraperOption.SELENIUM:
            try:
                driver.get(url)
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                raw_html = driver.page_source
            finally:
                driver.quit()
        elif option == ScraperOption.REQUESTS:
            response = requests.get(url, timeout=timeout)
            raw_html = response.text
        return raw_html
    except Exception as e:
        logger.error(f"Error getting raw HTML from URL: {e}")
        raise e


def save_html_to_file(html: str, directory: str, file_name: str) -> str:
    """
    Save the HTML to a file

    Parameters
    ----------
    html : str
        The HTML to save to the file
    directory : str
        The directory to save the file to
    file_name : str
        The name of the file to save the HTML to

    Returns
    -------
    str
        The path to the file where the HTML was saved
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    auto_create_dir(directory)
    file_name = f"{directory}/file_{timestamp}.html"
    try:
        with open(file_name, "w") as f:
            logger.info(f"Saving HTML to {file_name}")
            f.write(html)
    except Exception as e:
        logger.error(f"Error saving HTML to file: {e}")
    return file_name


def save_appliance_categories(directory: str, appliance_type: str) -> str | None:
    """
    Save the appliance categories to a file

    Parameters
    ----------
    directory : str
        The directory to save the appliance categories to
    appliance_type : str
        The type of appliance to get the brands for

    Returns
    -------
    str
        The path to the file where the appliance categories were saved
    """
    appliance_type = appliance_type.upper()

    appliance_url = f"{WEBSITE_URL}/{appliance_type}"
    raw_html = get_html_content(appliance_url)
    partitioned_dir = datetime.datetime.now().strftime("%Y%m%d")
    if raw_html:
        return save_html_to_file(
            raw_html,
            f"{directory}/{partitioned_dir}/{appliance_type}",
            "appliance_brands",
        )
    return None
