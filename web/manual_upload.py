import boto3
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = "airbyte-motherduck-hackathon"
SUPPORTED_BRANDS = ["LG", "ASKO", "BEKO", "SAMSUNG"]


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
    # st.set_page_config(
    #     page_title="Appliance Ocelot Manual upload 🛠️🧽", page_icon=":dishwasher:", layout="wide"
    # )
    # Container for main content
    with st.container():
        st.title("Welcome to Appliance Ocelot's User Manual Upload")
        st.markdown(
            "**Seamlessly upload the user manuals for your electrical appliance.**"
        )

    # Container for brand selection
    with st.container():
        st.header("Select a Brand")
        brands = SUPPORTED_BRANDS
        selected_brand = st.selectbox("brands", brands)

    # Container for file upload
    with st.container():
        st.header("Upload User Manual")
        uploaded_file = st.file_uploader(
            "Choose a user manual (PDF only):", type=["pdf"]
        )

    # Button to trigger upload
    upload_button = st.button(label="Upload + parse File")

    # Upload logic
    if upload_button and uploaded_file is not None and selected_brand:
        # Upload file to S3
        upload_to_s3(
            uploaded_file, BUCKET_NAME, selected_brand
        )  # Replace with your actual bucket name
    elif upload_button and selected_brand and not uploaded_file:
        st.warning("Please select a file to upload. ⚠️")
    elif upload_button and uploaded_file and not selected_brand:
        st.warning("Please select a brand. ⚠️")
