import datetime
import os

import boto3
import streamlit as st
from google import genai

model_name: str = "gemini-2.0-flash-exp"

# Initialize the Gemini client (do this outside the function for efficiency)
try:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    st.error("Please set the GEMINI_API_KEY environment variable.")
    st.stop()  # Stop execution if the API key is not set


def upload_to_s3(file, bucket_name, brand, object_name=None):
    """Uploads a file to an S3 bucket

    Args:
        file: The file to upload
        bucket_name: The S3 bucket to upload to
        brand: The brand of the dishwasher
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
                            if hasattr(part, "text"):  # Check if the part has text
                                yield part.text
            elif response.prompt_feedback:
                if (
                    response.prompt_feedback.block_reason
                ):  # Check if the prompt was blocked
                    st.error(
                        f"Gemini API Error: Prompt was blocked: {response.prompt_feedback.block_reason}"
                    )
                    return
            elif (
                response.usage_metadata
            ):  # If there is usage metadata there is no error
                continue
            else:
                st.error(f"Gemini API Error: Unknown error format: {response}")
                return
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return


def app():
    st.title("Dishwasher Repair Chatbot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "user_id" not in st.session_state:
        st.session_state.user_id = (
            "user123"  # Generate a unique ID if you have user accounts
        )

    if "dishwasher_model" not in st.session_state:
        st.session_state.dishwasher_model = None

    models = ["Model A", "Model B", "Model C"]  # Get this from your data
    selected_model = st.selectbox("Select your dishwasher model:", models)
    st.session_state.dishwasher_model = selected_model

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_question := st.chat_input(
        "Hello there! Anuja from Dishwasher here, how can I help?"
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
                You are friendly chatbot, working for a dishwasher service company
                **Task:**
                Act like a conversational human, don't be too verbose but still answer the User's question here:

                {user_question}
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
            "user_id": st.session_state.user_id,
            "dishwasher_model": st.session_state.dishwasher_model,
            "messages": st.session_state.messages,
            "metadata": {
                "gemini_prompt": user_question,  # The prompt is the user question
                "gemini_response_time": (end_time - start_time).total_seconds(),
            },
        }
        # save_chat_log(chat_log)
