import streamlit as st
import openai
import streamlit as st
from langchain.llms import OpenAI
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from langchain.document_loaders import PyPDFLoader
import base64
import pandas as pd
load_dotenv()


def json_to_dataframe_b(json_data):
    return pd.json_normalize(json_data)

def json_to_dataframe(json_data):
    # Extract data from the JSON
    customer_info = json_data.get("newBookingConfirmation", {}).get("customerInformation", {})
    booking_info = json_data.get("newBookingConfirmation", {}).get("bookingInformation", {})
    routing_info = json_data.get("newBookingConfirmation", {}).get("routingInstruction", {})
    airport_info = json_data.get("newBookingConfirmation", {}).get("airportInformation", {})
    
    # Create a list to store DataFrames
    dfs = []

    # Populate the list with DataFrames
    dfs.append(pd.DataFrame({"Category": ["NEW BOOKING CONFIRMATION"], "Attribute": [""], "Value": [""]}))
    
    dfs.append(pd.DataFrame({"Category": ["CUSTOMER INFORMATION"], "Attribute": ["NAME"], "Value": [customer_info.get("name", "")]}))
    dfs.append(pd.DataFrame({"Category": ["CUSTOMER INFORMATION"], "Attribute": ["TEL"], "Value": [customer_info.get("tel", "")]}))
    dfs.append(pd.DataFrame({"Category": ["CUSTOMER INFORMATION"], "Attribute": ["ADDRESS"], "Value": [customer_info.get("address", "")]}))
    
    dfs.append(pd.DataFrame({"Category": ["BOOKING INFORMATION"], "Attribute": ["AIR WAYBILL NO."], "Value": [booking_info.get("airWaybillNo", {}).get("master", "")]}))
    dfs.append(pd.DataFrame({"Category": ["BOOKING INFORMATION"], "Attribute": ["REFERENCE NUMBER"], "Value": [booking_info.get("referenceNumber", "")]}))
    
    dfs.append(pd.DataFrame({"Category": ["ROUTING INSTRUCTION"], "Attribute": ["COMMODITY"], "Value": [routing_info.get("commodity", "")]}))
    
    dfs.append(pd.DataFrame({"Category": ["AIRPORT INFORMATION"], "Attribute": ["AIRPORT OF DEPARTURE"], "Value": [airport_info.get("departure", "")]}))
    dfs.append(pd.DataFrame({"Category": ["AIRPORT INFORMATION"], "Attribute": ["AIRPORT OF DESTINATION"], "Value": [airport_info.get("destination", "")]}))

    # Concatenate the DataFrames
    result_df = pd.concat(dfs, ignore_index=True)
    
    return result_df
prompt="""
Please extract information from the provided text, which is extracted from a PDF file of airfreight labels, manifests, house air waybills, or trucking bills of lading. The extracted data should be formatted into the given JSON structure.If any values from the structured json is missing remove that alos in the output. The output must strictly be in JSON format without any additional text before or after it. Use only the values from the given text, and if a value is not available, please input "N/A" for that respective field. It's crucial to strictly adhere to the values present in the provided text.

Text: {}

"""

prompt_2="""

RESPONSE FORMAT
--------------
{
    "wayBill": "",
    "shipmentNumber": "",
    "origin": {
        "airportCode": "",
        "portCode": ""
    },
    "destination": {
        "airportCode": "",
        "portCode": ""
    },
    "pickupDetails": {
        "companyName": "",
        "address": "",
        "city": "",
        "stateOrZip": "",
        "contactInfo": {
            "contactName": "",
            "contactPhone": ""
        },
        "pickupTimeWindow": {
            "startTime": "",
            "endTime": ""
        },
        "accountNumber": ""
    },
    "deliveryDetails": {
        "receiverName": "",
        "address": "",
        "city": "",
        "stateOrZip": "",
        "contactInfo": {
            "contactName": "",
            "contactPhone": ""
        },
        "deliveryTimeWindow": {
            "startTime": "",
            "endTime": ""
        },
        "billingInfo": {
            "billingName": "",
            "billingAddress": "",
            "billingCity": "",
            "billingStateOrZip": "",
            "billingAccountNumber": ""
        },
        "cargoDetails": {
            "pieceCount": "",
            "itemDescription": "",
            "referenceNumbers": "",
            "classification": "",
            "grossWeight": "",
            "dimensionalWeight": "",
            "dimensions": "",
            "bookedWeight": "",
            "additionalServices": "",
            "specialInstructions": ""
        }
    }
}
	


RESPONSE:

"""
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
        return [remove_na_values(item) for item in data if item != 'N/A']
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

st.set_page_config(page_title="Freight Document Data Extraction Tool", page_icon="📄")


api_key_openai = os.getenv('OPENAI_API_KEY')  # Replace with your environment variable name

if api_key_openai:
    openai.api_key = api_key_openai
else:
    st.write("Please set your OpenAI API Key in the .env file")

st.title('Freight Document Data Extraction Tool')

uploaded_file = st.file_uploader("", key="file_uploader", accept_multiple_files=False, type="pdf")

if st.button("Upload and Extract Data"):
    if uploaded_file:
        with st.spinner('Extracting data...'):
            bytes_data = uploaded_file.read()
            _, file_extension = os.path.splitext(uploaded_file.name)
            with open(uploaded_file.name, "wb") as f:
                f.write(bytes_data)
            loader = PyPDFLoader(uploaded_file.name)
            data = loader.load()
            st.session_state.text = data[0].page_content
            os.remove(uploaded_file.name)

        prompt_in = prompt.format(st.session_state.text) + prompt_2

        if api_key_openai and st.session_state.text:
            final = get_final_data(prompt_in)
            st.write(final)
            #dataframe = json_to_dataframe(final)  # Convert JSON to DataFrame
            #transposed_dataframe = dataframe.T  # Transpose the DataFrame
            #st.dataframe(dataframe)
