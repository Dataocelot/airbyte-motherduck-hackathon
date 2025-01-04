import datetime
import json
import os
from pathlib import Path

import google.generativeai as genai
import pymupdf
import pymupdf4llm
from pymupdf import Document

from utils import (
    JSON_PG_NUM_PROMPT,
    TOC_IMAGE_PROMPT,
    ExtractorOption,
    Logger,
    PageContentSearchType,
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
def create_model(model_name: str = "gemini-2.0-flash-exp", **kwargs):
    """
    Create a generative model using the specified model name and configuration.

    Parameters
    ----------
    model_name : str
        The name of the model to create.
    kwargs : dict
        Additional keyword arguments to configure the model.

    Returns
    -------
    GenerativeModel
        The created generative model.
    """
    generation_config = kwargs

    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
    )
    return model


gemini_model_2_0_flash_exp = create_model(
    temperature=1,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
    response_mime_type="application/json",
)

EXPECTED_TOC_OUTPUT = """
            {
                "section_name": {
                    "page_number": int,
                    "subsections": {
                        "subsection_name": int,
                        "subsection_name2": int
                    }
                },
                "section_name2": {
                    "page_number": int,
                    "subsections": {
                        "subsection_name": int
                    }
                }
            }
"""

EXPECTED_TROBULESHOOTING_OUTPUT = "{subsection_name: [start_page_number, end_page_number], subsection_name2: [start_page_number, end_page_number]}"


def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini.

    See https://ai.google.dev/gemini-api/docs/prompting_with_media
    """
    try:
        file = genai.upload_file(path, mime_type=mime_type)
        logger.info(f"Uploaded file '{file.display_name}' as: {file.uri}")
        if file:
            return file
        else:
            logger.error("File upload failed, no file returned.")
            return None
    except Exception as e:
        logger.error(f"Failed to upload file to Gemini: {e}")
        return None


def extract_using_gemini(
    src_file_uri, mime_type, prompt, dest_filename, **kwargs
) -> dict | None:
    """
    Extract details using GEMINI

    Parameters
    ----------
    src_file_uri : str
        The URI of the file to extract details from
    mime_type : str
        The MIME type of the file
    prompt : str
        The prompt to use to extract details
    dest_filename : str
        The name of the file to save the extracted details to
    kwargs : dict
        Optional keyword arguments to format the prompt

    Returns
    -------
    dict|None
        The extracted details or None if an error occurred
    """

    try:
        if "parts" in kwargs:
            parts = kwargs["parts"]
        else:
            file = upload_to_gemini(src_file_uri, mime_type=mime_type)
            parts = [file, prompt.format(**kwargs)]

        chat_session = gemini_model_2_0_flash_exp.start_chat(
            history=[
                {"role": "user", "parts": parts},
            ]
        )
        response = chat_session.send_message("pathob\n")
        try:
            json_response = json.loads(response.text)
            save_dict_to_json(
                json_response, Path(src_file_uri).parent / f"{dest_filename}.txt"
            )
            return json_response
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            return None
    except Exception as e:
        logger.error(f"Error extracting details using GEMINI: {e}")
        return None


class ManualSection:
    def __init__(
        self,
        title: str,
        page_uris: list[str],
        page_start: int,
        page_end: int,
        document: "Document",
        source_type: SourceTypeOption,
    ):
        self.title = title
        self.page_uris = page_uris
        self.page_start = page_start
        self.page_end = page_end
        self.document = document
        self.source_type = source_type

    def __repr__(self):
        return (
            f"ManualSection("
            f"title='{self.title}', "
            f"page_uris='{self.page_ursi}', "
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
            f"Find the document(s) at {self.page_uris}"
        )


class TocSection(ManualSection):
    def __init__(
        self,
        title: str,
        page_uris: list[str],
        page_start: int,
        page_end: int,
        document: "Document",
        source_type: SourceTypeOption,
        extraction_type: SourceTypeOption,
        destination_type: SourceTypeOption,
        toc_mapping: dict,
        simplified_toc_mapping: dict,
    ):
        super().__init__(title, page_uris, page_start, page_end, document, source_type)
        self.extraction_type = extraction_type
        self.destination_type = destination_type
        self.toc_mapping = toc_mapping
        self.simplified_toc_mapping = simplified_toc_mapping

    def __repr__(self):
        return f"""
            TocSection(
                title={self.title}
                page_uris={self.page_uris},
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
            f"Find the document(s) at {self.page_uris}"
            f"Extraction process {self.source_type.name} -> {self.extraction_type.name} -> {self.destination_type.name}"
        )


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

    def _extract_to_markdown(self, document: Document) -> str:
        """
        Extract a Document to Markdown

        Parameters
        ----------
        document : Document
            The Document to extract to Markdown
        """
        return pymupdf4llm.to_markdown(document)

    def extract_all_subsections(self, section_mapping: dict) -> dict:
        """
        Extract all subsections from the section mapping

        Parameters
        ----------
        section_mapping : dict
            The mapping of sections to subsections

        Returns
        -------
        dict
            The mapping of all subsections to their page numbers
        """
        all_subsections = {}
        for _, details in section_mapping.items():
            for subsection, page_number in details["subsections"].items():
                all_subsections[subsection] = page_number
        result = {}
        for i, (key, value) in enumerate(all_subsections.items()):
            if i == len(all_subsections) - 1:
                result[key] = [value, None]
            else:
                result[key] = [value, value + 1]
        return result

    def _get_consecutive_pages(self, page_matches):
        pg_no_matches = []
        previous_page = None
        for current_page, current_value in page_matches.items():
            if current_value:
                if previous_page is not None:
                    if previous_page + 1 == current_page:
                        pg_no_matches.append(previous_page)
                        pg_no_matches.append(current_page)
                else:
                    pg_no_matches.append(current_page)
            previous_page = current_page if current_value else None
        return list(set(pg_no_matches))

    def _get_pages_with_content(
        self,
        search_content: str,
        pages_to_search: int | list = 5,
        search_method: PageContentSearchType = PageContentSearchType.CONSECUTIVE_PAGES,
    ) -> list[pymupdf.Page] | None:
        """
        Get the pages with the content

        Parameters
        ----------
        search_content : str
            The content to search for in the pages
        pages_to_search : int | list, optional
            The maximum page(s) to search in the PDF, by default 5
        search_method : str, optional
            The method to use to search for the content, by default PageContentSearchType.CONSECUTIVE_PAGES
        Returns
        -------
        list[pymupdf.Page] | None
            The pages with the content or None if the content was not found
        """

        if isinstance(pages_to_search, int):
            pages_search_list = range(pages_to_search)
            if pages_to_search > len(self.document):
                logger.info(
                    "Pages to search exceeds the number of pages in the document, so searching all pages"
                )
                pages_search_list = range(len(self.document))

        page_matches = {
            i: self.document[i].search_for(search_content) for i in pages_search_list
        }

        logger.info(page_matches)

        pg_no_matches: list = []
        if search_method == PageContentSearchType.EARLIEST_PAGE_FIRST:
            if page_matches:
                for page_match in page_matches:
                    if page_matches[page_match]:
                        pg_no_matches.append(page_match)
                        break

        elif search_method == PageContentSearchType.CONSECUTIVE_PAGES:
            pg_no_matches = self._get_consecutive_pages(page_matches)

        if pg_no_matches:
            logger.info(
                f"The search content with {search_content} most likely on page {pg_no_matches}"
            )
            pages = [self.document[page_no] for page_no in pg_no_matches]
            return pages
        logger.error(f"Could not find {search_content} in the Document")
        return None

    def save_search_content_to_img(
        self, filepath: Path | str, search_content, pages_to_search: int | list = 5
    ) -> list:
        """
        Save the searched content pages to image(s)

        Parameters
        ----------
        search_content : str
            The content to search for in the pages
        pages_to_search : int, list, optional
            The maximum page(s) to search in the PDF, by default 5
        """
        saved_paths = []
        try:
            self.matched_pages = self._get_pages_with_content(
                search_content=search_content, pages_to_search=pages_to_search
            )
            if self.matched_pages:
                for matched_page in self.matched_pages:
                    pix = matched_page.get_pixmap()
                    save_to_path = f"{filepath}_{matched_page.number}.png"
                    pix.save(save_to_path)
                    saved_paths.append((matched_page, save_to_path))
                    logger.info(save_to_path)
        except Exception as e:
            logger.error(f"Error saving table of contents to image: {e}")
        return saved_paths

    def _extract_toc_from_img(self) -> TocSection | None:
        if self.toc_mapping_method == ExtractorOption.GEMINI:
            try:
                pages_uris = self.save_search_content_to_img(
                    self.toc_path / "toc", search_content="contents"
                )
                toc_mappings = {}
                for _, uri in pages_uris:
                    toc_mapping = extract_using_gemini(
                        src_file_uri=uri,
                        mime_type="image/png",
                        dest_filename="toc_mapping",
                        prompt=TOC_IMAGE_PROMPT,
                        file_type="image",
                        device=self.device,
                        dest_file_type="JSON",
                        expected_output=EXPECTED_TOC_OUTPUT,
                    )
                    if toc_mapping:
                        toc_mappings.update(toc_mapping)

                if toc_mappings:
                    page_start = pages_uris[0][0]
                    page_end = pages_uris[-1][0]
                    simplified_toc_map = self.extract_all_subsections(toc_mappings)
                    toc_details = TocSection(
                        title="TOC",
                        page_uris=pages_uris,
                        page_start=page_start,
                        page_end=page_end,
                        document=self.document,
                        source_type=SourceTypeOption.PDF,
                        extraction_type=SourceTypeOption.IMAGE,
                        destination_type=SourceTypeOption.JSON,
                        toc_mapping=toc_mappings,
                        simplified_toc_mapping=simplified_toc_map,
                    )
                    save_dict_to_json(
                        simplified_toc_map,
                        self.toc_path / "simplified_toc_mapping.txt",
                    )
                    logger.info("Table of contents extracted")
                return toc_details
            except Exception as e:
                logger.error(f"Error extracting TOC using GEMINI: {e}")

        elif self.toc_mapping_method == ExtractorOption.PYMUPDF:
            # TODO: Implement text extraction from the table of contents using PyMuPDF.
            pass
        return None

    def estimate_troubleshooting_sections(self):
        # needed to get the toc as json
        toc_details = self._extract_toc_from_img()

        if toc_details:
            est_troubleshooting_pages = extract_using_gemini(
                src_file_uri=self.toc_path / "simplified_toc_mapping.txt",
                mime_type="text/plain",
                dest_filename="troubleshooting_page",
                prompt=JSON_PG_NUM_PROMPT,
                file_type="json",
                device=self.device,
                subject_of_interest="troubleshooting",
                dest_file_type="JSON",
                expected_output=EXPECTED_TROBULESHOOTING_OUTPUT,
            )
            return est_troubleshooting_pages
