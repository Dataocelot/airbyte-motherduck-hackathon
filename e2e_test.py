from pathlib import Path

from helper.utils import Environment, ExtractorOption
from pdfprocessor.parser import PdfManualParser

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
        environment=Environment.LOCAL,
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
