from helper.utils import Environment, ExtractorOption
from pdfprocessor.parser import PdfManualParser

file_path_1 = "data/manuals/LG/MFL66281402.pdf"
file_path_2 = "data/manuals/ASKO/489319.pdf"
file_path_3 = "data/manuals/LG/DW_EUK_MFL71916115_02_230720_00_OM_WEB.pdf"
file_path_4 = "data/manuals/LG/DW_EUK_MFL72141208_00_240522_00_OM_WEB.pdf"
file_path_5 = "data/manuals/MIELE/G4203SCusermanual.pdf"
file_path_6 = "data/manuals/BEKO/21383_dfn-1000-i_gb_booklet.pdf"

pdf_parser = PdfManualParser(
    pdf_path=file_path_4,
    model_number="DF243",
    brand="LG",
    device="Dishwasher",
    environment=Environment.AWS,
    toc_mapping_method=ExtractorOption.GEMINI,
)

# # trblshoot_sections_map = pdf_parser.get_subject_of_interest_section_map(
#     "troubleshooting", "troubleshooting_page"
# )
# print(trblshoot_sections_map)

pdf_parser.get_subject_of_interest_section_map(
    "device care instructions", "troubleshooting_page"
)
pdf_parser.extract_all_sections_content()
pdf_parser.cleanup()
