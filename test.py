import streamlit as st
import tempfile
import os
from PIL import Image
from encoder import encode_image
from decoder import decode_image
from encodeVideo import encode_video_with_cv2
from decodeVideo import decode_video_with_cv2

# Function to handle file processing based on selection
def handle_file_upload(selected_option, uploaded_file, text_file=None, lsb_bits=1, selected_format="AVI"):
    if uploaded_file is not None:
        # storing the uploaded file details
        file_details = {
            "Filename": uploaded_file.name,
            "FileType": uploaded_file.type,
            "FileSize": uploaded_file.size
        }
        st.write(f"Processing {selected_option} with {lsb_bits} LSB bits:")

        # Create a temporary file to store the uploaded video file (if video is selected)
        if "Video" in selected_option:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video_file:
                temp_video_file.write(uploaded_file.read())  # Write the uploaded file's content to the temp file
                temp_video_path = temp_video_file.name  # Get the path of the temp file

        if "Encode Image" in selected_option:
            # Open and display the image
            if text_file is not None:
                text_file_details = {
                    "Filename": text_file.name,
                    "FileType": text_file.type,
                    "FileSize": text_file.size
                }
                # Encode the image with text file
                encoded_img = encode_image(uploaded_file, text_file, lsb_bits)
                st.image(encoded_img, caption='Encoded Image', use_column_width=True)

                # Save or provide download link for encoded image
                encoded_img_path = "encoded_image.png"
                encoded_img.save(encoded_img_path)
                st.download_button("Download Encoded Image", data=open(encoded_img_path, "rb").read(), file_name=encoded_img_path)

        elif "Decode Image" in selected_option:
            try:
                message = decode_image(uploaded_file, lsb_bits)
                st.write("Decoded Message:")
                st.markdown(f'<p style="font-size:48px;">{message}</p>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"An error occurred during decoding: {e}")

        elif "Encode Video" in selected_option:
            if text_file is not None:
                # Create a temporary file to store the uploaded text file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_text_file:
                    temp_text_file.write(text_file.read())  # Write the uploaded text file's content to the temp file
                    temp_text_path = temp_text_file.name  # Get the path of the temp text file

                # Adding a spinner while the video is being encoded
                with st.spinner(f"Encoding video with payload to {selected_format} format..."):
                    try:
                        output_filename = f"encoded_video.{selected_format.lower()}"
                        final_output_path = encode_video_with_cv2(temp_video_path, temp_text_path, output_filename, lsb_bits, selected_format)
                    except Exception as e:
                        st.error(f"An error occurred during video encoding: {e}")
                        return

                # Check if the file exists before allowing download
                if final_output_path and os.path.exists(final_output_path):
                    st.download_button("Download Encoded Video", data=open(final_output_path, "rb").read(), file_name=os.path.basename(final_output_path))
                else:
                    st.warning("Encoded video could not be saved or found.")

        elif "Decode Video" in selected_option:
            try:
                # Use the temp video path for decoding
                with st.spinner("Decoding video to retrieve payload..."):
                    message = decode_video_with_cv2(temp_video_path, lsb_bits, selected_format)

                st.write("Decoded Message:")
                st.markdown(f'<p style="font-size:48px;">{message}</p>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"An error occurred during decoding: {e}")

        elif "Audio" in selected_option:
            st.warning("Audio encoding/decoding not implemented yet.")
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
options = ["Encode Image", "Decode Image", "Encode Video", "Decode Video", "Encode Audio", "Decode Audio"]
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

# Dropdown for selecting output format for encoding/decoding video
if "Encode Video" in selected_option:
    formats = ["AVI", "MOV"]  # Lossless formats for encoding
    selected_format = st.selectbox("Select the output format", formats)

elif "Decode Video" in selected_option:
    # For decoding, only lossless formats should be allowed
    lossless_formats = ["AVI", "MOV"]  # Limit to lossless formats
    selected_format = st.selectbox("Select the input format", lossless_formats)

# File uploader widget with dynamic keys to ensure reset
uploaded_file = None
text_file = None

# Use unique keys for the file uploader to ensure it's reset
if "Image" in selected_option:
    uploaded_file = st.file_uploader("Upload an Image", type=["png", "jpg", "jpeg", "bmp", "gif"], key=f"image_uploader_{selected_option}")
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Image', use_column_width=True)

        if "Encode Image" in selected_option:
            text_file = st.file_uploader("Upload a Text File", type=["txt"], key=f"text_file_uploader_{selected_option}")
            if text_file:
                st.session_state.text_file = text_file

elif "Video" in selected_option:
    uploaded_file = st.file_uploader("Upload a Video File", type=["mp4", "avi", "mov", "mpeg"], key=f"video_uploader_{selected_option}")
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file

        if "Encode Video" in selected_option:
            text_file = st.file_uploader("Upload a Text File", type=["txt"], key=f"text_file_uploader_{selected_option}")
            if text_file:
                st.session_state.text_file = text_file

elif "Audio" in selected_option:
    uploaded_file = st.file_uploader("Upload an Audio File", type=["mp3", "wav", "flac"], key=f"audio_uploader_{selected_option}")
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file

# Button to submit the selected option and file
if st.button("Submit"):
    handle_file_upload(selected_option, st.session_state.uploaded_file, st.session_state.text_file, st.session_state.lsb_bits, selected_format if "Encode Video" in selected_option or "Decode Video" in selected_option else None)
