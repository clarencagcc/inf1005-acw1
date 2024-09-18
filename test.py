import streamlit as st
from PIL import Image
from encoder import encode_image
from decoder import decode_image

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

        if "Encode Image" in selected_option:
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
        elif "Decode Image" in selected_option:
            try:
                message = decode_image(uploaded_file, lsb_bits)
                st.write("Decoded Message:")
                st.markdown(f'<p style="font-size:48px;">{message}</p>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"An error occurred during decoding: {e}")
        elif "Audio" in selected_option:
            # TODO AUDIO LOGIC
            pass
    else:
        st.warning("Please upload a file to proceed.")

# Streamlit UI components
st.title("Encode/Decode Application")

# Initialize session state variables if not already present
if 'selected_option' not in st.session_state:
    st.session_state.selected_option = "Encode Image"
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'text_file' not in st.session_state:
    st.session_state.text_file = None
if 'lsb_bits' not in st.session_state:
    st.session_state.lsb_bits = 1
    

# Dropdown menu for selecting options
options = ["Encode Image", "Decode Image", "Encode Audio", "Decode Audio"]
selected_option = st.selectbox("Select an action", options, index=options.index(st.session_state.selected_option))

# Update session state when dropdown selection changes
if st.session_state.selected_option != selected_option:
    st.session_state.selected_option = selected_option
    st.session_state.uploaded_file = None
    st.session_state.text_file = None
    st.session_state.lsb_bits = 1  # Reset the slider value when changing options

# Slider to select the number of LSB bits
lsb_bits = None
if "Encode" in selected_option or "Decode" in selected_option:
    lsb_bits = st.slider("Select the number of LSB bits", min_value=1, max_value=8, value=st.session_state.lsb_bits)
    st.session_state.lsb_bits = lsb_bits  # Update session state

# File uploader widget with dynamic keys to ensure reset
uploaded_file = None
text_file = None

# Use unique keys for the file uploader to ensure it's reset
if "Image" in selected_option:
    uploaded_file = st.file_uploader("Upload an Image", type=["png", "jpg", "jpeg", "bmp", "gif"], key=f"image_uploader_{selected_option}")
    if uploaded_file:
        # making sure to show original image before moving on to encoding.
        st.session_state.uploaded_file = uploaded_file
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image', use_column_width=True)

        if "Encode Image" in selected_option:
            text_file = st.file_uploader("Upload a Text File", type=["txt"], key=f"text_file_uploader_{selected_option}")
            if text_file:
                st.session_state.text_file = text_file
        
elif "Audio" in selected_option:
    uploaded_file = st.file_uploader("Upload an Audio File", type=["mp3", "wav", "flac"], key=f"audio_uploader_{selected_option}")
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file

# Button to submit the selected option and file
if st.button("Submit"):
    handle_file_upload(selected_option, st.session_state.uploaded_file, st.session_state.text_file, st.session_state.lsb_bits)
