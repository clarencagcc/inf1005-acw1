import streamlit as st
from PIL import Image
from encoder import encode_image

# Function to handle file processing based on selection
def handle_file_upload(selected_option, uploaded_file, text_file=None, lsb_bits=1):
    if uploaded_file is not None:
        # storing the uploaded file details
        file_details = {
            "Filename": uploaded_file.name,
            "FileType": uploaded_file.type,
            "FileSize": uploaded_file.size
        }
        st.write(f"Processing {selected_option} with {lsb_bits} LSB bits:")

        if "Image" in selected_option:
            # Open and display the image            
            if text_file is not None:
                text_file_details = {
                    "Filename": text_file.name,
                    "FileType": text_file.type,
                    "FileSize": text_file.size
                }
                # Encode the image with text file
                encoded_img = encode_image(uploaded_file, text_file, lsb_bits) # passing the image, uploaded payload .txt file and the no. lsb_bits
                st.image(encoded_img, caption='Encoded Image', use_column_width=True) # displaying encoded image before downloading
                
                # Save or provide download link for encoded image
                encoded_img_path = "encoded_image.png"
                encoded_img.save(encoded_img_path) # save to main directory
                st.download_button("Download Encoded Image", data=open(encoded_img_path, "rb").read(), file_name=encoded_img_path)
        elif "Audio" in selected_option:
            # TODO AUDIO LOGIC
            pass
    else:
        st.warning("Please upload a file to proceed.")

# Streamlit UI components
st.title("Encode/Decode Application")

# Dropdown menu for selecting options
options = ["Encode Image", "Decode Image", "Encode Audio", "Decode Audio"]
selected_option = st.selectbox("Select an action", options)

# Slider to select the number of LSB bits
lsb_bits = None
if "Encode" in selected_option:
    lsb_bits = st.slider("Select the number of LSB bits", min_value=1, max_value=8, value=1)

# File uploader widget with drag-and-drop support
uploaded_file = None
text_file = None

if "Image" in selected_option:
    uploaded_file = st.file_uploader("Upload an Image", type=["png", "jpg", "jpeg", "bmp", "gif"], key="image_uploader")
    if uploaded_file:
        # making sure to show original image before moving on to encoding.
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image', use_column_width=True)
        
        # Show text file uploader if image is uploaded only after uploading an image
        text_file = st.file_uploader("Upload a Text File", type=["txt"], key="text_file_uploader")
elif "Audio" in selected_option:
    uploaded_file = st.file_uploader("Upload an Audio File", type=["mp3", "wav", "flac"])

# Button to submit the selected option and file
if st.button("Submit"):
    handle_file_upload(selected_option, uploaded_file, text_file if 'text_file' in locals() else None, lsb_bits if lsb_bits is not None else 1)
