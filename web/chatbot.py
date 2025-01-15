import datetime
import os
import sys

import boto3
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from dotenv import load_dotenv
from google import genai
from yaml.loader import SafeLoader

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_utils import get_duckdb_conn, is_table_exists

from helper.logger import Logger
from helper.utils import TROUBLESHOOTING_CONTENT_QUERY, get_airtable_table

load_dotenv()

FALLBACK_RESPONSE = "Apologies, for the issue you are currently experiencing. One of our technicians will get in touch with you"

# Initialize logger
logger_instance = Logger()
logger = logger_instance.get_logger()

proj_dir = os.path.dirname(__file__)

motherduck_conn = get_duckdb_conn("my_db", os.environ["MOTHERDUCK_API_KEY"])
is_table_created = is_table_exists(motherduck_conn, "my_db", "manual_sections")

try:
    with open(f"{proj_dir}/auth.yml") as file:
        config = yaml.load(file, Loader=SafeLoader)
        logger.info("Loaded Auth file")
except Exception as e:
    logger.exception(f"Unable to read yaml file {e}")


model_name: str = "gemini-2.0-flash-exp"

try:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    logger.info("Set Gemini client")
except KeyError as keyerror:
    logger.exception(f"Issue setting up Gemini client {keyerror}")
    st.error("Please set the GEMINI_API_KEY environment variable.")
    st.stop()


def upload_to_s3(file, bucket_name, brand, object_name=None):
    """Uploads a file to an S3 bucket

    Args:
        file: The file to upload
        bucket_name: The S3 bucket to upload to
        brand: The brand
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


def generate_text_with_gemini_stream(prompt, model="gemini-pro"):
    """Generates text using Gemini with streaming and robust error handling."""
    try:
        response_stream = client.models.generate_content_stream(
            model=model, contents=prompt
        )
        for response in response_stream:
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, "text"):
                                yield part.text
            elif response.prompt_feedback:
                if response.prompt_feedback.block_reason:
                    st.error(
                        f"Gemini API Error: Prompt was blocked: {response.prompt_feedback.block_reason}"
                    )
                    return
            elif response.usage_metadata:
                continue
            else:
                st.error(f"Gemini API Error: Unknown error format: {response}")
                return
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return


def app():
    st.title("Anuja (Your favourite repair Chatbot)")
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )
    authenticator.login()

    if "disabled" not in st.session_state:
        st.session_state.disabled = False

    if st.session_state["authentication_status"]:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "username" not in st.session_state:
            authenticator.login()

        if "appliance_model" not in st.session_state:
            st.session_state.appliance_model = None

        def disable():
            st.session_state.disabled = is_table_created

        # Airtable
        cs_accounts_table_obj = get_airtable_table(
            table_id=os.environ["AIRTABLE_CUSTOMER_ACCOUNTS_TABLE_ID"]
        )
        cs_product_table_obj = get_airtable_table(
            table_id=os.environ["AIRTABLE_PRODUCT_TABLE_ID"]
        )

        cs_accounts = cs_accounts_table_obj.all(
            fields=["Product Category", "Email", "Product Model Number", "Brand Name"]
        )

        for cs_account in cs_accounts:
            if cs_account["fields"]["Email"] == st.session_state["username"]:
                break
        cs_product = cs_product_table_obj.get(
            cs_account["fields"]["Product Category"][0],
        )

        cs_product_name = cs_product["fields"]["Name"]
        cs_product_brand_name = cs_account["fields"]["Brand Name"][0]

        cs_model_name = cs_account["fields"]["Product Model Number"][0]
        selected_product = st.selectbox("Select your Product:", cs_product_name)
        selected_model_number = st.selectbox("Select your Product:", cs_model_name)
        st.session_state.product = selected_product
        st.session_state.model_number = selected_model_number
        # Airtable

        query = TROUBLESHOOTING_CONTENT_QUERY.format(
            model_number=cs_model_name,
            device=cs_product_name,
            brand=cs_product_brand_name,
        )

        logger.info(f"Query: {query}")
        try:
            troubleshooting_content = motherduck_conn.query(query).fetchall()[0][0]
        except IndexError:
            troubleshooting_content = FALLBACK_RESPONSE
        except duckdb.duckdb.CatalogException:
            troubleshooting_content = "No user manuals parsed yet, so can't give response, try uploading and then syncing"
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if user_question := st.chat_input(
            "Hello there! 👋🏿 Anuja here, how can I help you today?",
            disabled=st.session_state.disabled,
            on_submit=disable,
        ):
            st.session_state.messages.append({"role": "user", "content": user_question})
            with st.chat_message("user"):
                st.markdown(user_question)

            with st.chat_message("assistant", avatar="👷🏽‍♀️"):
                message_placeholder = st.empty()
                full_response = ""
                start_time = datetime.datetime.now()
                for text_chunk in generate_text_with_gemini_stream(
                    f"""Task:
                    You are friendly support chatbot for helping customers troubleshoot given a user manual
                    If unsure ask user to contact support via phone
                    **Task:**
                    Act like a conversational human, don't be too verbose but still answer the User's question here, given context:

                    ```User question
                    {user_question}
                    ```

                    ```Context
                    {troubleshooting_content}
                    ```
                    """,
                    model_name,
                ):
                    full_response += text_chunk
                    message_placeholder.markdown(
                        full_response + "▌"
                    )  # Add a cursor for effect
                message_placeholder.markdown(full_response)
                end_time = datetime.datetime.now()

            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )

            chat_log = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "user_id": st.session_state.username,
                "model_number": st.session_state.model_number,
                "product": st.session_state.product,
                "messages": st.session_state.messages,
                "metadata": {
                    "gemini_prompt": user_question,
                    "gemini_response_time": (end_time - start_time).total_seconds(),
                },
            }
            # save_chat_log(chat_log)
        elif st.session_state["authentication_status"] is False:
            st.error("Username/password is incorrect")
        elif st.session_state["authentication_status"] is None:
            st.warning("Please enter your username and password")
