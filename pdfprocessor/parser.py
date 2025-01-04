import datetime
import json
import os
from pathlib import Path

import google.generativeai as genai
import pymupdf
import pymupdf4llm
import requests
from bs4 import BeautifulSoup
from pymupdf import Document
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import (
    TOC_IMAGE_PROMPT,
    ExtractorOption,
    Logger,
    ScraperOption,
    SourceTypeOption,
    auto_create_dir,
    save_dict_to_json,
)

# Initialize logger
logger_instance = Logger()
logger = logger_instance.get_logger()


# Configure GEMINI
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
)


def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini.

    See https://ai.google.dev/gemini-api/docs/prompting_with_media
    """
    try:
        file = genai.upload_file(path, mime_type=mime_type)
        logger.info(f"Uploaded file '{file.display_name}' as: {file.uri}")
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        if file:
            return file
        else:
            logger.error("File upload failed, no file returned.")
            return None
    except Exception as e:
        logger.error(f"Failed to upload file to Gemini: {e}")
        return None


# def prompt_gemini_with_file(file, prompt):
#     """Prompts Gemini with the given file and prompt.

#     See https://ai.google.dev/gemini-api/docs/prompting_with_media
#     """
#     if file.mimeType in ("png", "jpeg" "jpg"):
#         file = upload_to_gemini(file, mime_type="image/{file.}")
#     chat_session = model.start_chat(
#         history=[
#             {
#                 "role": "user",
#                 "parts": [
#                     file,
#                     TOC_IMAGE_PROMPT.format(device=self.device),
#                 ],
#             },
#         ]
#     )
#     response = chat_session.send_message("pathob\n")


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


# def save_appliance_categories(directory: str, appliance_type: str) -> str | None:
#     """
#     Save the appliance categories to a file

#     Parameters
#     ----------
#     directory : str
#         The directory to save the appliance categories to
#     appliance_type : str
#         The type of appliance to get the brands for

#     Returns
#     -------
#     str
#         The path to the file where the appliance categories were saved
#     """
#     appliance_type = appliance_type.upper()

#     appliance_url = f"{WEBSITE_URL}/{appliance_type}"
#     raw_html = get_html_content(appliance_url)
#     partitioned_dir = datetime.datetime.now().strftime("%Y%m%d")
#     if raw_html:
#         return save_html_to_file(
#             raw_html,
#             f"{directory}/{partitioned_dir}/{appliance_type}",
#             "appliance_brands",
#         )
#     return None


class ManualSection:
    def __init__(
        self,
        title: str,
        page_uri: str,
        page_start: int,
        page_end: int,
        document: "Document",
        source_type: SourceTypeOption,
    ):
        self.title = title
        self.page_uri = page_uri
        self.page_start = page_start
        self.page_end = page_end
        self.document = document
        self.source_type = source_type

    def __repr__(self):
        return (
            f"ManualSection("
            f"title='{self.title}', "
            f"page_uri='{self.page_uri}', "
            f"page_start={self.page_start}, "
            f"page_end={self.page_end}, "
            f"document={self.document}, "
            f"source_type={self.source_type.name}"
            f")"
        )

    def __str__(self):
        return (
            f"Manual Section of '{self.title}' spanning pages "
            f"{self.page_start} to {self.page_end}. "
            f"Find the document at {self.page_uri}"
        )


class TocSection(ManualSection):
    def __init__(
        self,
        title: str,
        page_uri: str,
        page_start: int,
        page_end: int,
        document: "Document",
        source_type: SourceTypeOption,
        extraction_type: SourceTypeOption,
        destination_type: SourceTypeOption,
        toc_mapping: dict,
    ):
        super().__init__(title, page_uri, page_start, page_end, document, source_type)
        self.extraction_type = extraction_type
        self.destination_type = destination_type
        self.toc_mapping = toc_mapping

    def __repr__(self):
        return f"""
            TocSection(
                title={self.title}
                page_uri={self.page_uri},
                page_start={self.page_start},
                page_end={self.page_end},
                document={self.page_end},
                source_type={self.source_type},
                extraction_type={self.extraction_type},
                destination_type={self.destination_type}
                toc_mapping={self.toc_mapping}
            )
        """

    def __str__(self):
        return (
            f"Manual Section of '{self.title}' spanning pages "
            f"{self.page_start} to {self.page_end}. "
            f"Find the document at {self.page_uri}"
            f"Extraction process {self.source_type.name} -> {self.extraction_type.name} -> {self.destination_type.name}"
        )


class SiteScraper:
    def __init__(self, site_name: str, site_url: str):
        self.site_name = site_name
        self.site_url = site_url

    def extract_collection_from_html(
        self,
        raw_html: str,
        class_name: str,
        element_name: str | None = None,
    ) -> list:
        """
        Extract the appliance brands from the raw HTML
        """
        soup = BeautifulSoup(raw_html, "html.parser")
        subcategories_section = soup.find_all(element_name, class_=class_name)
        return subcategories_section

    def get_html_content(
        self, scraper_option: ScraperOption | None = None
    ) -> str | None:
        """
        Get the raw HTML from the URL

        Parameters
        ----------
        scraper_option : ScraperOption (optional)
            The option to use to get the HTML (default is ScraperOption.REQUESTS)

        Returns
        -------
        str|None
            Raw HTML from the URL or None if an error occurred
        """
        if scraper_option:
            return get_html_content(self.site_url, option=scraper_option)
        return get_html_content(self.site_url)

    def get_toc_details(self, raw_html: str) -> list:
        """
        Get the table of contents details from the raw HTML
        """
        toc_details = self.extract_collection_from_html(raw_html, "toc", "div")
        return toc_details


class PdfManualParser:
    def __init__(
        self,
        pdf_path: str,
        device: str,
        toc_mapping_method: ExtractorOption,
        output_path: str | Path | None = None,
    ):
        self.pdf_path = Path(pdf_path)
        self.filename = self.pdf_path.stem
        self.toc_mapping_method = toc_mapping_method
        self.document = pymupdf.open(self.pdf_path)
        self.device = device
        self.root_data_dir, _, self.brand, _ = Path(self.pdf_path).parts

        if output_path:
            self.output_path = output_path
        else:

            date = datetime.datetime.now().strftime("%Y-%m-%d")
            output_path = (
                Path(self.root_data_dir)
                / "output"
                / f"brand={self.brand}"
                / f"date={date}"
                / f"{self.filename}"
            )

            self.toc_path = output_path / "toc"
            auto_create_dir(self.toc_path)

            self.troubleshooting_path = output_path / "troubleshooting"
            auto_create_dir(self.troubleshooting_path)

            self.output_path = output_path

    def extract_to_markdown(self):
        self.markdown_text = pymupdf4llm.to_markdown(self.document)

    def _get_toc_page(self, max_page_to_search: int = 5) -> pymupdf.Page:
        page_matches = {
            i: self.document.search_page_for(i, text="contents")
            for i in range(max_page_to_search)
        }
        highest_pg_matches = max(page_matches.items(), key=lambda x: x[1])

        if page_no := highest_pg_matches[0]:
            logger.info(f"Table of contents most likely on page {page_no}")
            toc_page = self.document[page_no]
            return toc_page
        else:
            logger.error("Could not find table of contents")

    def save_toc_to_img(self, max_page_to_search: int = 5) -> str | None:
        """
        Save the table of contents as an image

        Parameters
        ----------
        max_page_to_search : int, optional
            The maximum page to search in the PDF, by default 5
        """
        save_to_path = None
        try:
            self.toc_page = self._get_toc_page(max_page_to_search)
            pix = self.toc_page.get_pixmap()
            save_to_path = f"{self.toc_path}/toc_{self.toc_page.number}.png"
            pix.save(save_to_path)
            logger.info(save_to_path)
        except Exception as e:
            logger.error(f"Error saving table of contents to image: {e}")
        return save_to_path

    def _extract_toc_img(self) -> TocSection | None:
        pass
        # TODO: change to function utility extract_img_to_json
        if self.toc_mapping_method == ExtractorOption.GEMINI:
            try:
                toc_page_img_uri = self.save_toc_to_img()
                if toc_page_img_uri:
                    file = upload_to_gemini(toc_page_img_uri, mime_type="image/png")
                    chat_session = model.start_chat(
                        history=[
                            {
                                "role": "user",
                                "parts": [
                                    file,
                                    TOC_IMAGE_PROMPT.format(
                                        device=self.device,
                                        file_type="image",
                                        result_type="JSON",
                                    ),
                                ],
                            },
                        ]
                    )
                    try:
                        toc_mapping = json.loads(response.text)
                    except json.JSONDecodeError:
                        toc_mapping = None
                    try:
                        toc_mapping = json.loads(response.text)
                        save_dict_to_json(
                            toc_mapping, f"{self.toc_path}/toc_mapping.json"
                        )

                        toc_details = TocSection(
                            title="TOC",
                            page_uri=toc_page_img_uri,
                            page_start=self.toc_page.number,
                            page_end=self.toc_page.number,
                            document=self.document,
                            source_type=SourceTypeOption.PDF,
                            extraction_type=SourceTypeOption.IMAGE,
                            destination_type=SourceTypeOption.JSON,
                            toc_mapping=toc_mapping,
                        )
                        logger.info("Table of contents extracted")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON response: {e}")
            except Exception as e:
                logger.error(f"Error extracting TOC using GEMINI: {e}")
                logger.error(e)
                logger.error(f"Error extracting TOC using GEMINI: {e}")

        elif self.toc_mapping_method == ExtractorOption.PYMUPDF:
            # TODO: Implement text extraction from the table of contents using PyMuPDF.
            # This will involve searching for the text "contents" in the first few pages,
            # extracting the text from the identified TOC page, and parsing the text to extract the TOC details.
            # TODO: Implement text extraction from the table of contents image using Tesseract OCR.
            # This will involve converting the image to text using Tesseract OCR,
            # and then parsing the extracted text to extract the TOC details.
            # TODO: Implement text extraction from the table of contents image using Tesseract OCR.
            # This will involve converting the image to text and then parsing the text to extract the TOC details.
            pass
        return toc_details

    def _extract_troubleshooting_to_md(self):
        pass
