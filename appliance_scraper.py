import requests
from bs4 import BeautifulSoup
from utils import auto_create_dir, Logger
import datetime

APPLIANCE_TYPE = 'Dryer'
WEBSITE_URL = f'https://www.ifixit.com/Device'
# https://www.appliancefactoryparts.com/dishwashers

logger_instance = Logger()
logger = logger_instance.get_logger()

def get_raw_html(url: str) -> str:
    """
    Get the raw HTML from a URL

    Parameters
    ----------
    url : str
        The URL to get the HTML from

    Returns
    -------
    str
        The raw HTML from the URL
    """
    r = requests.get(url)
    logger.info(f"GET request to {url} returned status code {r.status_code}")
    return r.text

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
        with open(file_name, 'w') as f:
            logger.info(f"Saving HTML to {file_name}")
            f.write(html)
    except Exception as e:
        logger.error(f"Error saving HTML to file: {e}")
    return file_name

def save_appliance_categories(appliance_type: str) -> str:
    """
    Save the appliance categories to a file

    Parameters
    ----------
    appliance_type : str
        The type of appliance to get the brands for

    Returns
    -------
    str
        The path to the file where the appliance categories were saved
    """
    appliance_type = appliance_type.capitalize()

    appliance_url = f"{WEBSITE_URL}/{appliance_type}"
    raw_html = get_raw_html(appliance_url)
    partitioned_dir = datetime.datetime.now().strftime("%Y%m%d")
    return save_html_to_file(raw_html, f'fixtures/{partitioned_dir}/{APPLIANCE_TYPE}', 'appliance_brands')

def extract_appliance_brands(raw_html: str, class_name: str = "subcategorySection") -> list:
    """
    Extract the appliance brands from the raw HTML
    """
    soup = BeautifulSoup(raw_html, 'html.parser')
    subcategories_section = soup.find_all('div', class_=class_name)
    # brands = soup.find_all('a', class_='guide-header')
    return subcategories_section
    # return [brand.text for brand in brands]

if __name__ == '__main__':
    saved_appliance_path = save_appliance_categories(APPLIANCE_TYPE)
    # saved_appliance_path = 'fixtures/20250101/Dishwasher/file_20250101_173107.html'
    with open(saved_appliance_path, 'r') as f:
        raw_html = f.read()
    brands = extract_appliance_brands(raw_html)
    print(brands)
