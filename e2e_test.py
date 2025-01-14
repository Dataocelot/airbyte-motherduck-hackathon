import os
from pathlib import Path

from dotenv import load_dotenv

from helper.utils import Environment, ExtractorOption
from pdfprocessor.parser import PdfManualParser

load_dotenv()

env_to_use = os.getenv("ENVIRONMENT", "LOCAL")
envs = {"AWS": Environment.AWS, "LOCAL": Environment.LOCAL}

file_details = [
    (file, file.stem, file.parent.name)
    for file in Path("dataset/manuals").glob("*/*.pdf")
]
for file_detail in file_details:
    pdf_parser = PdfManualParser(
        pdf_path=str(file_detail[0]),
        model_number=file_detail[1],
        brand=file_detail[2],
        device="Dishwasher",
        environment=envs[env_to_use],
        toc_mapping_method=ExtractorOption.GEMINI,
    )

    trblshoot_sections_map = pdf_parser.get_subject_of_interest_section_map(
        "troubleshooting", "troubleshooting_page"
    )
    print(trblshoot_sections_map)

    pdf_parser.get_subject_of_interest_section_map(
        "device care instructions", "troubleshooting_page"
    )
    pdf_parser.extract_all_sections_content()
    pdf_parser.cleanup()
    break
