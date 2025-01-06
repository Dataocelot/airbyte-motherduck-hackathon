import json
import os
import tempfile
from pathlib import Path

import google.generativeai as genai
import pymupdf
import pymupdf4llm
from pymupdf import Document

from utils import (
    JSON_PG_NUM_PROMPT,
    TOC_IMAGE_PROMPT,
    Environment,
    ExtractorOption,
    Logger,
    PageContentSearchType,
    SourceTypeOption,
    auto_create_dir,
    get_hash_from_file,
    get_object_from_s3,
    save_dict_to_json,
    save_file_to_s3,
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

EXPECTED_SECTION_MAP_OUTPUT = "{subsection_name: [page_start_number, end_page_number], subsection_name2: [page_start_number, end_page_number]}"


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


def extract_doc_map_using_gemini(
    src_filepath,
    mime_type,
    prompt,
    dest_filename,
    environment: Environment = Environment.LOCAL,
    **kwargs,
) -> dict | None:
    """
    Extract the document map using GEMINI

    Parameters
    ----------
    src_filepath : str
        The URI of the file to extract details from
    mime_type : str
        The MIME type of the file
    prompt : str
        The prompt to use to extract details
    dest_filename : str
        The name of the file to save the extracted details to
    environment : Environment
        The Environment, local or AWS, default is Local
    kwargs : dict
        Optional keyword arguments to format the prompt

    Returns
    -------
    dict|None
        The extracted details or None if an error occurred
    """

    file = src_filepath
    try:
        if "parts" in kwargs:
            parts = kwargs["parts"]
        else:
            if environment == environment.AWS:
                file = get_object_from_s3(src_filepath)
                logger.info(
                    f"Retrieved this file {src_filepath} from S3 and saved here {file}"
                )

        uploaded_file = upload_to_gemini(file, mime_type=mime_type)
        parts = [uploaded_file, prompt.format(**kwargs)]

        chat_session = gemini_model_2_0_flash_exp.start_chat(
            history=[
                {"role": "user", "parts": parts},
            ]
        )
        response = chat_session.send_message("pathob\n")
        try:
            json_response = json.loads(response.text)
            save_dict_to_json(json_response, Path(file).parent / f"{dest_filename}.txt")
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
        model_number: str | None,
        output_path: str | Path | None = None,
        environment: Environment = Environment.LOCAL,
    ):
        self.pdf_path = Path(pdf_path)
        self.filename = self.pdf_path.stem
        self.toc_mapping_method = toc_mapping_method
        self.environment = environment
        self.document = pymupdf.open(self.pdf_path)
        self.document_hash = get_hash_from_file(pdf_path)
        self.device = device
        self.model_number = model_number
        self.root_data_dir, _, self.brand, _ = Path(self.pdf_path).parts
        if output_path:
            self.output_path = output_path
        else:
            if environment == Environment.LOCAL:
                self.root_dir = Path(self.root_data_dir)
            if environment == Environment.AWS:
                self.temp_file_dir = tempfile.TemporaryDirectory()
                self.root_dir = Path(self.temp_file_dir.name)

            self.relative_dir = (
                Path("output")
                / f"brand={self.brand}"
                / f"model_number={self.model_number}"
            )

            self.output_path = self.root_dir / self.relative_dir

            self.document_mapping_path = Path("document_map")
            self.parsed_sections_path = Path("sections")

            auto_create_dir(self.output_path / self.document_mapping_path)
            auto_create_dir(self.output_path / self.parsed_sections_path)

            logger.info(
                f"Output path: {self.output_path}, root_dir: {self.root_dir}, Environment {environment}"
            )

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
                f"I searched and found `{search_content}` most likely on page {pg_no_matches}"
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
            filepath = Path(filepath)
            if self.matched_pages:
                for matched_page in self.matched_pages:
                    pix = matched_page.get_pixmap()

                    if self.environment == Environment.AWS:
                        save_to_path = f"{self.relative_dir}/{filepath.name}_{matched_page.number}.png"
                        save_file_to_s3(
                            pix.pil_tobytes(format="PNG"),
                            save_to_path,
                            content_type="image/png",
                        )
                        logger.info(
                            f"Saved Searched contents Image result to the S3 Bucket: {save_to_path}"
                        )
                    elif self.environment == Environment.LOCAL:
                        save_to_path = f"{filepath}_{matched_page.number}.png"
                        pix.save(save_to_path)
                    saved_paths.append((matched_page, save_to_path))
        except Exception as e:
            logger.error(f"Error Searched contents as an image: {e}")
        return saved_paths

    def _extract_toc_map_from_img(self) -> TocSection | None:
        if self.toc_mapping_method == ExtractorOption.GEMINI:
            try:
                if self.environment == Environment.LOCAL:
                    base_path = self.output_path / self.document_mapping_path
                elif self.environment == Environment.AWS:
                    base_path = self.output_path / self.document_mapping_path
                pages_uris = self.save_search_content_to_img(
                    base_path / "toc_map",
                    search_content="contents",
                )
                toc_mappings = {}
                for _, uri in pages_uris:
                    toc_mapping = extract_doc_map_using_gemini(
                        src_filepath=uri,
                        mime_type="image/png",
                        dest_filename="toc_mapping",
                        prompt=TOC_IMAGE_PROMPT,
                        file_type="image",
                        device=self.device,
                        dest_file_type="JSON",
                        environment=self.environment,
                        expected_output=EXPECTED_TOC_OUTPUT,
                    )
                    if toc_mapping:
                        toc_mappings.update(toc_mapping)

                if toc_mappings:
                    toc_json_string = json.dumps(toc_mappings)
                    toc_json_bytes = toc_json_string.encode("utf-8")
                    save_dict_to_json(
                        toc_mappings,
                        self.output_path
                        / self.document_mapping_path
                        / "toc_mapping.txt",
                    )
                    save_file_to_s3(
                        toc_json_bytes,
                        self.relative_dir
                        / self.document_mapping_path
                        / "toc_mapping.txt",
                    )
                    logger.info("Saving Table of contents to S3")

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
                    self.toc_details_dict = toc_details

                    save_dict_to_json(
                        simplified_toc_map,
                        self.output_path
                        / self.document_mapping_path
                        / "simplified_toc_mapping.txt",
                    )
                    if self.environment == Environment.AWS:
                        # Convert the dictionary to a JSON string
                        json_string = json.dumps(simplified_toc_map)
                        json_bytes = json_string.encode("utf-8")
                        logger.info("Saving Simplified Table of contents to S3")

                        save_file_to_s3(
                            json_bytes,
                            self.relative_dir
                            / self.document_mapping_path
                            / "simplified_toc_mapping.txt",
                        )
                    logger.info("Table of contents extracted and Saved")

                return toc_details
            except Exception as e:
                logger.error(f"Error extracting TOC using GEMINI: {e}")

        elif self.toc_mapping_method == ExtractorOption.PYMUPDF:
            # TODO: Implement text extraction from the table of contents using PyMuPDF.
            pass
        return None

    def get_subject_of_interest_section_map(
        self, subject_of_interest: str, dest_filename: str
    ):
        if not hasattr(self, "toc_details_dict"):
            self.toc_details = self._extract_toc_map_from_img()

        if self.toc_details:
            # fmt: off
            toc_simplified_mapping_path = self.document_mapping_path / "simplified_toc_mapping.txt"
            # fmt: on

            if self.environment == Environment.LOCAL:
                src_filepath = self.output_path / toc_simplified_mapping_path
            elif self.environment == Environment.AWS:
                src_filepath = self.relative_dir / toc_simplified_mapping_path

            est_section_map = extract_doc_map_using_gemini(
                src_filepath=src_filepath,
                mime_type="text/plain",
                dest_filename=dest_filename,
                prompt=JSON_PG_NUM_PROMPT,
                file_type="json",
                device=self.device,
                subject_of_interest=subject_of_interest,
                dest_file_type="JSON",
                environment=self.environment,
                expected_output=EXPECTED_SECTION_MAP_OUTPUT,
            )
            return est_section_map
        return None

    def extract_section_content(
        self, section_name: str, page_start: int, page_end: int | None
    ) -> dict | None:
        """
        Extracts a section given the page numbers and the section name

        Parameters
        ----------
        section_name : str
            The name of the section to extract
        page_start : int
            The starting page of the section
        page_end : int | None
            The ending page of the section

        Returns
        -------
        dict | None
            A dictionary with the section name and the markdown content of the section, else None
        """
        if not page_end:
            page_end = len(self.document) - 1
        page_nums = range(page_start, page_end)
        try:
            md_text = pymupdf4llm.to_markdown(self.document, pages=[*page_nums])
            result = {
                "brand": self.brand,
                "section_name": section_name,
                "markdown_text": md_text,
                "document_hash": self.document_hash,
                "model_number": self.model_number,
                "device": self.device,
            }
            logger.info(
                f"Successfully extracted Markdown for {section_name}, {page_start} -> {page_end}"
            )
            return result
        except Exception as markdownexception:
            logger.error(f"Error getting Markdown for Document {markdownexception}")
        return None

    def extract_all_sections_content(self) -> list:
        result = []
        if not hasattr(self, "toc_details_dict"):
            self.toc_details = self._extract_toc_map_from_img()
        if self.toc_details_dict:
            for (
                section_name,
                page_span,
            ) in self.toc_details_dict.simplified_toc_mapping.items():
                result.append(self.extract_section_content(section_name, *page_span))
            logger.info("Extracted all contents found in the Table of contents")
        return result

    def cleanup(self):
        try:
            if self.environment == Environment.AWS:
                self.temp_file_dir.cleanup()
            else:
                os.remove(self.root_data_dir)
        except Exception as e:
            logger.error(f"Issue cleaning up files {e}")
