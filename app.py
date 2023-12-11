

import streamlit as st
from pdf2image import convert_from_path
from PIL import Image
import tempfile
import openai
import streamlit as st
import requests
import pdfkit
import time
from langchain.llms import OpenAI
import pinecone
import os
import PyPDF2
from PyPDF2 import PdfReader
from openai import OpenAI
from langchain.memory import MongoDBChatMessageHistory
from langchain.prompts import PromptTemplate
from streamlit_chat import message
import json
from langchain.document_loaders import PyPDFLoader
import base64


prompt="""
Please extract information from the provided text, which is extracted from a PDF file of airfreight labels, manifests, house air waybills, or trucking bills of lading. The extracted data should be formatted into the given JSON structure. The output must strictly be in JSON format without any additional text before or after it. It's crucial to strictly adhere to the values present in the provided text.

Text: {}

"""
prompt_2="""
    RESPONSE FORMAT
    --------------
   {
    "key1": "",
    "key2":"",
    "key3":"",
    "key4":"",
    
    }

 RESPONSE:   
"""
# prompt_2="""

# RESPONSE FORMAT
# --------------
# {
#     "shipmentNumber": "",
#     "origin": {
#         "airportCode": "",
#         "portCode": ""
#     },
#     "destination": {
#         "airportCode": "",
#         "portCode": ""
#     },
#     "pickupDetails": {
#         "companyName": "",
#         "address": "",
#         "city": "",
#         "stateOrZip": "",
#         "contactInfo": {
#             "contactName": "",
#             "contactPhone": ""
#         },
#         "pickupTimeWindow": {
#             "startTime": "",
#             "endTime": ""
#         },
#         "accountNumber": ""
#     },
#     "deliveryDetails": {
#         "receiverName": "",
#         "address": "",
#         "city": "",
#         "stateOrZip": "",
#         "contactInfo": {
#             "contactName": "",
#             "contactPhone": ""
#         },
#         "deliveryTimeWindow": {
#             "startTime": "",
#             "endTime": ""
#         },
#         "billingInfo": {
#             "billingName": "",
#             "billingAddress": "",
#             "billingCity": "",
#             "billingStateOrZip": "",
#             "billingAccountNumber": ""
#         },
#         "cargoDetails": {
#             "pieceCount": "",
#             "itemDescription": "",
#             "referenceNumbers": "",
#             "classification": "",
#             "grossWeight": "",
#             "dimensionalWeight": "",
#             "dimensions": "",
#             "bookedWeight": "",
#             "additionalServices": "",
#             "specialInstructions": ""
#         }
#     }
# }


# RESPONSE:

# """
def get_response_from_openai(prompt_in):
  try:
    # print(prompt_in)

    client = OpenAI()

    response = client.chat.completions.create(
      model="gpt-3.5-turbo-1106",
      messages=[
        {
          "role": "user",
          "content": prompt_in
        }
      ],
      temperature=1,
      max_tokens=3000,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    # return response.choices[0].text
    return response.choices[0].message.content
  except Exception as e:
    print(e)

def get_final_data(prompt_new):
    try:
        st.session_state.loading = True
        out=get_response_from_openai(prompt_new)
        x=json.loads(out)
        cleaned_data = remove_na_values(x)
        cleaned_json = json.dumps(cleaned_data, indent=4)
        y=json.loads(cleaned_json)
        st.session_state.loading = False
        return y
    except:
        st.session_state.loading = False
        return "Internal error with Open AI"
    
def remove_na_values(data):
   
    if isinstance(data, dict):
        return {k: remove_na_values(v) for k, v in data.items() if v != 'N/A'}
    elif isinstance(data, list):
        return [remove_na_values(item) for item in data]
    else:
        return data
    
def get_pdf_display_string(pdf_path):
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display_string = f"data:application/pdf;base64,{base64_pdf}"
    return pdf_display_string


client = openai


if "text" not in st.session_state:
    st.session_state.text = ""

if "loading" not in st.session_state:
    st.session_state.loading = False
# if "thread_id" not in st.session_state:
#     st.session_state.thread_id = None

# if 'selected_items' not in st.session_state:
#     st.session_state['selected_items'] = []

st.set_page_config(page_title="ChatGPT-like Chat App", page_icon=":speech_balloon:")


st.sidebar.header("Opean ai Configuration")
api_key_openai = st.sidebar.text_input("Enter your OpenAI API key", type="password")
if api_key_openai:
    openai.api_key = api_key_openai
    os.environ['OPENAI_API_KEY'] = api_key_openai

else:
   st.write("Please add your OpenAI API Key")


uploaded_file = st.sidebar.file_uploader("Upload a file", key="file_uploader",accept_multiple_files=False, type="pdf")
x= 0
if st.sidebar.button("Upload File"):
    x = 1
    if uploaded_file:
            bytes_data =uploaded_file.read()
            _ , file_extension = os.path.splitext(uploaded_file.name)
            with open(uploaded_file.name,"wb") as f:
                f.write(bytes_data)
            loader = PyPDFLoader(uploaded_file.name)
            data=loader.load()
            st.session_state.text=data[0].page_content
            os.remove(uploaded_file.name)


prompt_in=prompt.format(st.session_state.text)+prompt_2
if api_key_openai and uploaded_file and st.session_state.text:
    if st.button('Extract Data'):
        with st.spinner('Extracting data...'):
            final= get_final_data(prompt_in)
        st.write(final)

