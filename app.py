import streamlit as st
import requests

st.set_page_config(page_title="Lab Test Extractor", page_icon="🧪", layout="centered")

st.title("🧪 Lab Report Extraction App")
st.write("Upload your lab report image and extract structured lab test data!")

uploaded_file = st.file_uploader("Choose an image file", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    if st.button("Extract Lab Tests"):
        with st.spinner('Processing...'):
            files = {"file": uploaded_file.getvalue()}
            response = requests.post("http://localhost:8000/get-lab-tests", files={"file": uploaded_file})
            
            if response.status_code == 200:
                data = response.json()
                if data.get("is_success"):
                    if data['data']:  # Only if extracted lab tests exist
                        st.success("Extraction Successful!")
                        st.subheader("Extracted Lab Tests:")

                        for test in data['data']:
                            st.json(test)
                    else:
                        st.warning("Extraction completed but no lab test data found. Please upload a clearer report.")
                else:
                    st.error(f"Failed: {data.get('error')}")

            else:
                st.error(f"API Error: {response.status_code}")
