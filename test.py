import streamlit as st

# Function to handle file processing based on selection
def handle_file_upload(selected_option, uploaded_file):
    if uploaded_file is not None:
        file_details = {
            "Filename": uploaded_file.name,
            "FileType": uploaded_file.type,
            "FileSize": uploaded_file.size
        }
        st.write(f"Processing {selected_option}:")
        st.json(file_details)
        # Add your encoding/decoding logic here
    else:
        st.warning("Please upload a file to proceed.")

# Streamlit UI components
st.title("Encode/Decode Application")

# Dropdown menu for selecting options
options = ["Encode Image", "Decode Image", "Encode Audio", "Decode Audio"]
selected_option = st.selectbox("Select an action", options)

# File uploader widget with drag-and-drop support
if "Image" in selected_option:
    uploaded_file = st.file_uploader("Upload an Image", type=["png", "jpg", "jpeg", "bmp", "gif"])
elif "Audio" in selected_option:
    uploaded_file = st.file_uploader("Upload an Audio File", type=["mp3", "wav", "flac"])

# Button to submit the selected option and file
if st.button("Submit"):
    handle_file_upload(selected_option, uploaded_file)
