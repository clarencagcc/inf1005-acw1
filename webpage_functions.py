import streamlit as st
import zipfile
import os
import io

from decode_encode_png import png_decode, png_encode
from decode_encode_wav import wav_decode, wav_encode
from encoder import encode_image
from audio_spectrogram import plot_spectrogram

MAX_IMAGE_HEIGHT = 600
MAX_TEXT_HEIGHT = 400

def encode_section():
    # Set the page configuration to use a wide layout
    st.set_page_config(layout="wide")

    # Set the title of the app
    st.title("Steganography Encoder/Decoder")

    st.markdown("## Encoding")

    # Use columns to make the layout cleaner
    col1, col2 = st.columns(2)

    # File uploader for Payload
    with col1:
        st.subheader("Payload")
        payload_file = st.file_uploader("Drag and drop file here", type=["txt"], key="payload")
        if payload_file:
            # Encode and decode because some characters (like em dash) aren't in the ascii table
            payload_content = payload_file.read().decode('ascii', 'ignore')

            st.text_area("Complete File Content:", payload_content, height=MAX_TEXT_HEIGHT)

    # File uploader for Cover
    with col2:
        st.subheader("Cover")
        cover_file = st.file_uploader("Drag and drop file here", type=["jpg", "png", "jpeg", "wav"], key="cover")
        if cover_file:
            # st.text_area("Type: ", cover_file.type)
            if cover_file.type == "image/jpg" or cover_file.type == "image/png" or cover_file.type == "image/jpeg":
                st.image(cover_file, width=MAX_IMAGE_HEIGHT)
            elif cover_file.type == "audio/wav":
                spectrogram_image = plot_spectrogram(cover_file)
                st.image(spectrogram_image, caption=f"Spectrogram")
                st.audio(cover_file)

    # Slider for selecting the number of LSB bits
    st.markdown("### LSB Bit Selection")
    encode_slider = st.slider("LSB bits used for encoding.", min_value=1, max_value=8, value=2, key='encode-slider')

    # Only show the button if there is already a cover_file and a payload_file
    if cover_file and payload_file:
        filename = cover_file.name.split('.')[0]
        extension = cover_file.type.split('/')[-1]

        # Buttons for Downloading single encoded file
        col1, col2 = st.columns(2)
        output_path = ""
        # Encode Button
        with col1:
            # Button to encode using selected LSB bits
            if st.button("Encode using selected LSB", key="encode-button"):
                if extension == "png" or extension == "jpg" or extension == "jpeg":
                    if extension == "png":
                        output = png_encode(cover_file, payload_content, encode_slider)
                    else:
                        output = encode_image(cover_file, payload_file, encode_slider)

                    try:
                        # Save image to local storage to download the file
                        output_path = f"output/{filename}.{encode_slider}.png"
                        output.save(output_path)
                    except Exception:
                        output_path = ""
                        st.write("Cover is too small to store payload.")
                elif extension == "wav":
                    try:
                        output_path = f"output/{filename}.{encode_slider}.wav"
                        wav_encode(cover_file, payload_content, output_path, encode_slider)
                    except Exception as e:
                        st.write(f"Error encoding WAV file: {e}")
        # Download Button
        with col2:
            if output_path != "":
                st.download_button("Download Encoded File",
                                   data=open(output_path, 'rb').read(),
                                   file_name=output_path,
                                   key='download-single')
        # Print Image below buttons
        if output_path != "" :
            if extension == ("png" or "jpg" or "jpeg"):
                col0, col1, col2, col3 = st.columns([1, 1, 1, 1])
                with col1:
                    st.header = "Original"
                    st.image(cover_file, width=MAX_IMAGE_HEIGHT)
                with col2:
                    st.header = "Encoded"
                    st.image(output, width=MAX_IMAGE_HEIGHT)
            if extension == "wav":
                st.audio(output_path)

        # Buttons for downloading multiple encoded files
        col1, col2 = st.columns(2)

        output_list = []
        output_paths = []
        # Encode Button
        with col1:
            # Button to encode from 1 LSB to 8 LSB
            if st.button("Encode from 1 LSB to 8 LSB", key="encode-multi"):
                # Encode the file for each LSB
                # Save all those generated files to output folder
                # store paths for each file
                # use those paths to generate slideshow
                if extension == "png":
                    for i in range(1, 9):
                        output = png_encode(cover_file, payload_content, i)
                        # png_encode will return bool during failure
                        if type(output) == bool:
                            st.write(f"{i} LSB is too small for this payload.")
                            continue
                        output_list.append(output)
                        # Save image to local storage to download the file
                        output_path = f"output/{filename}.{i}.png"
                        output.save(output_path)
                        output_paths.append(output_path)
                elif extension == "jpg" or extension == "jpeg":
                    for i in range(1, 9):
                        try:
                            output = encode_image(cover_file, payload_file, i)
                            output_list.append(output)
                            # Save image to local storage to download the file
                            output_path = f"output/{filename}.{i}.png"
                            output.save(output_path)
                        except Exception:
                            st.write(f"{i} LSB is too small for this payload.")
                elif extension == "wav":
                    for i in range (1, 9):
                        try:
                            # st.write(f"Current LSB value: {i} (Type: {type(i)})")
                            output_path = f"output/{filename}.{i}.wav"
                            #st.write("path done")
                            cover_file = io.BytesIO(cover_file.getvalue())  # Reset file stream for each loop iteration
                            #st.write("reset stream")
                            output = wav_encode(cover_file, payload_content, output_path, i)
                            output_list.append(output)
                            output_paths.append(output_path)
                        except Exception as e:
                            st.write(f"Error encoding WAV file: {e}")

        # Download button
        with col2:
            # Different file types have different render steps
            if extension in ["png", "jpg", "jpeg", "wav"]:
                if len(output_paths) > 0:
                    zip_buffer = io.BytesIO()
                    # Add each file (image or wav) to zip folder
                    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                        for file_path in output_paths:
                            # Read the file in binary mode
                            with open(file_path, "rb") as file:
                                zip_file.writestr(os.path.basename(file_path), file.read())  # Add file to zip

                    # After writing to the zip, we need to seek to the beginning of the buffer
                    zip_buffer.seek(0)

                    st.download_button(
                        label="Download All Files",
                        data=zip_buffer,
                        file_name=f"{filename}.zip",
                        mime="application/zip"
                    )

        # Create slider to switch between different images
        mult_encode_output_count = len(output_list)
        if mult_encode_output_count > 0:
            if extension in ["png", "jpg", "jpeg", "wav"]:
                # Handle both images and WAV files in a row layout
                if extension in ["png", "jpg", "jpeg"]:
                    cols = st.columns(mult_encode_output_count)
                    for idx, col in enumerate(cols):
                        with col:
                            st.write(8 - mult_encode_output_count + 1 + idx)
                            st.image(output_list[idx], width=200)
                elif extension == "wav":
                    for idx in range(mult_encode_output_count):
                        st.write(8 - mult_encode_output_count + 1 + idx)
                        # For WAV files, plot and display the spectrogram
                        spectrogram_image = plot_spectrogram(output_paths[idx])
                        st.image(spectrogram_image, caption=f"Spectrogram {idx + 1}")
                        st.audio(output_paths[idx])


def decode_section():
    st.markdown("## Decoding")

    # Use columns to make the layout cleaner
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Encoded File")
        encoded_file = st.file_uploader("Encoded file to use.", type=["png", "wav"], key="encoded_file")

    with col2:
        if encoded_file and encoded_file.type == "png":
            st.image(encoded_file, width=MAX_IMAGE_HEIGHT)

    st.markdown("### LSB Bit Selection")
    decode_slider = st.slider("LSB bits used for encoding.", min_value=1, max_value=8, value=2, key='decode-slider')

    if encoded_file:
        if st.button("Decode File", key='decode-button'):
            extension = encoded_file.type.split('/')[1]
            if extension == "png":
                decoded_content = png_decode(encoded_file, decode_slider)
                st.text_area("Complete File Content:", decoded_content, height=MAX_TEXT_HEIGHT, key="decode-text-area")
            elif extension == "wav":
                try:
                    decoded_content = wav_decode(encoded_file, decode_slider)
                    st.text_area("Complete File Content:", decoded_content, height=MAX_TEXT_HEIGHT, key="decode-text-area")
                except Exception as e:
                    st.write(f"Error decoding WAV file: {e}")