import os
import sys
import tempfile

import boto3
import streamlit as st
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from helper.utils import Environment, ExtractorOption, Logger
from pdfprocessor.parser import PdfManualParser

load_dotenv()

# Initialize logger
logger_instance = Logger()
logger = logger_instance.get_logger()

env_to_use = os.getenv("ENVIRONMENT", "LOCAL")
envs = {"AWS": Environment.AWS, "LOCAL": Environment.LOCAL}

BUCKET_NAME = "airbyte-motherduck-hackathon"
SUPPORTED_BRANDS = ["ASKO", "BEKO", "LG", "SAMSUNG"]
DEVICES = ["Dishwasher", "TV", "Washing Machines"]


def upload_to_s3(file, bucket_name, brand, object_name=None):
    """Uploads a file to an S3 bucket

    Args:
        file: The file to upload
        bucket_name: The S3 bucket to upload to
        brand: The electronic brand
        object_name: The S3 object name. If not specified, file.name will be used
    """
    if object_name is None:
        object_name = f"dataset/{brand.upper()}/{file.name}"  # Add brand to object key
    s3_client = boto3.client("s3")
    try:
        s3_client.upload_fileobj(file, bucket_name, object_name)
        st.success("File uploaded 🎉")
    except Exception as e:
        st.error(f"Error uploading file: {e}")


def app():
    with st.container():
        st.title("Welcome to Ocelot Living User Manual Upload")
        st.markdown(
            "**Seamlessly upload the user manuals for your electrical appliance.**"
        )
    # TODO: rename
    # Container for brand selection
    with st.container():
        st.header("Select a Brand")
        brands = SUPPORTED_BRANDS
        selected_brand = st.selectbox("brands", brands)

    with st.container():
        st.header("Select a Brand")
        model_number = st.text_input("model_number")

    with st.container():
        st.header("Select a Device")
        brands = SUPPORTED_BRANDS
        devices = DEVICES
        selected_device = st.selectbox("devices", devices)

    # Container for file upload
    with st.container():
        st.header("Upload User Manual")
        uploaded_file = st.file_uploader(
            "Choose a user manual (PDF only):", type=["pdf"]
        )

    # Button to trigger upload
    upload_button = st.button(label="Upload + Parse")

    if upload_button and uploaded_file is not None and selected_brand:
        # upload_to_s3(uploaded_file, BUCKET_NAME, selected_brand)
        # logger.info(uploaded_file)

        # Save the uploaded file to the specified path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            logger.info(temp_file.name)
            pdf_parser = PdfManualParser(
                pdf_path=temp_file.name,
                model_number=model_number,
                brand=selected_brand,
                device=selected_device,
                environment=envs[env_to_use],
                toc_mapping_method=ExtractorOption.GEMINI,
            )
            pdf_parser.temp_file_path = temp_file.name
            pdf_parser.extract_all_sections_content()
            pdf_parser.cleanup()

    elif upload_button and selected_brand and not uploaded_file:
        st.warning("Please select a file to upload. ⚠️")
    elif upload_button and uploaded_file and not selected_brand:
        st.warning("Please select a brand. ⚠️")
