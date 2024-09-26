import streamlit as st
import zipfile
import os
import io
import tempfile

from decode_encode_png import png_decode, png_encode
from decode_encode_wav import wav_decode, wav_encode
from decode_encode_flac import flac_decode, flac_encode
from decode_encode_mkv import mkv_encode, mkv_decode
from encodeVideo import encode_video_with_cv2
from decodeVideo import decode_video_with_cv2
from encoder import encode_image
from audio_spectrogram import plot_spectrogram

from PIL import Image
from pydub import AudioSegment
import moviepy.editor as mp

MAX_IMAGE_HEIGHT = 400
MAX_TEXT_HEIGHT = 400

from pydub.utils import which
AudioSegment.converter = which("ffmpeg")

def create_temp_file(mkv_file):
    # Create a temporary file with a unique path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mkv") as temp_file:
        mkv_file.seek(0)
        # Write the uploaded file's content to the temporary file
        temp_file.write(mkv_file.read())
        temp_file_path = temp_file.name
        return temp_file_path


def convert_cover_to_selected_format(cover_file, selected_format):
    cover_extension = cover_file.type.split('/')[-1]
    selected_format = selected_format.lower()
    # Create a temporary file to store the converted output
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{selected_format}") as temp_output:
        output_path = temp_output.name
        temp_output.flush()

        try:
            # Handle image conversion
            if cover_file.type in ["image/jpg", "image/png", "image/jpeg", "image/webp"]:
                img = Image.open(cover_file)
                img.save(output_path, selected_format.upper())

            # Handle audio conversion
            elif cover_file.type in ["audio/wav", "audio/flac"]:
                audio = AudioSegment.from_file(cover_file, format=cover_extension)
                audio.export(output_path, format=selected_format)

            # Handle video conversion
            elif cover_file.type in ["video/x-matroska", "video/avi", "video/quicktime", "video/mp4"]:
                video_codec = ""
                if cover_file.type in ["video/avi", "video/quicktime"]:
                    video_codec = "ffv1"
                else:
                    video_codec = "libx264"

                tempfile_path = create_temp_file(cover_file)
                clip = mp.VideoFileClip(tempfile_path)
                clip.write_videofile(output_path, codec=video_codec, audio_codec="aac", preset="ultrafast")

            return output_path
        except Exception as e:
            st.error(f"convert_cover_to_selected_format() Error: {e}")

def encode_section_choose_files():
    # Use columns to make the layout cleaner
    col1, col2 = st.columns(2)
    output_format = []
    selected_format = None

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
        cover_file = st.file_uploader("Drag and drop file here", type=["jpg", "png", "jpeg", 'webp',
                                                                       "wav", "flac",
                                                                       "mkv", 'avi', 'mov', "mp4"], key="cover")
        if cover_file:
            # uncomment this line to see what your file type is
            # st.write("Type: ", cover_file.type)
            if cover_file.type in ["image/jpg", "image/png", "image/jpeg", "image/webp"]:
                output_format = ['PNG']
                st.image(cover_file, width=MAX_IMAGE_HEIGHT)

            elif cover_file.type in ["audio/wav"]:
                output_format = ['FLAC', 'WAV']
                spectrogram_image = plot_spectrogram(cover_file)
                st.image(spectrogram_image, caption=f"Spectrogram")
                st.audio(cover_file)

            elif cover_file.type in ["audio/flac"]:
                output_format = ['FLAC', 'WAV']
                spectrogram_image = plot_spectrogram(cover_file)
                st.image(spectrogram_image, caption=f"Spectrogram")
                st.audio(cover_file)

            elif cover_file.type in ["video/x-matroska", "video/avi", "video/quicktime", "video/mp4"]:
                output_format = ['MKV', "AVI", "MOV"]  # Lossless formats for encoding
                preview_file = convert_cover_to_selected_format(cover_file, "mp4")
                st.video(preview_file)

            selected_format = st.selectbox("Select the output format", output_format)

    return cover_file, payload_file, selected_format


def encode_section_single_encode(cover_file, payload_file, encode_slider, selected_format):
    col1, col2 = st.columns(2)

    # Move the pointer back to the start of the file so that we can read it again from the beginning
    payload_file.seek(0)
    payload_content = payload_file.read().decode('ascii', 'ignore')
    filename = cover_file.name.split('.')[0]
    extension = cover_file.type.split('/')[-1]

    # Convert file to selected format
    cover_file.seek(0)
    tempfile = convert_cover_to_selected_format(cover_file, selected_format)
    selected_format = selected_format.lower()

    output_path = ""
    output = None

    # Encode Button
    with col1:
        #st.write(extension)
        if st.button("Encode using selected LSB", key="encode-button"):
            if selected_format in ["png", "webp"]:
                output = png_encode(tempfile, payload_content, encode_slider)
                try:
                    # Save image to local storage to download the file
                    output_path = f"output/{filename}.{encode_slider}.{selected_format}"
                    output.save(output_path, loessless=True)
                except Exception as e:
                    output_path = ""
                    st.error(f"Cover file may be too small.")
                    st.error(f"Error encoding PNG/WEBP file: {e}")
            elif selected_format in ["jpg", "jpeg"]:
                output = encode_image(tempfile, payload_file, encode_slider)
                try:
                    # Save image to local storage to download the file
                    output_path = f"output/{filename}.{encode_slider}.png"
                    output.save(output_path)
                except Exception as e:
                    output_path = ""
                    st.error(f"Cover file may be too small.")
                    st.error(f"Error encoding JPEG file: {e}")
            elif selected_format in "flac":
                try:
                    output_path = f"output/{filename}.{encode_slider}.flac"
                    flac_encode(tempfile, output_path, payload_content, encode_slider)
                except Exception as e:
                    output_path = ""
                    st.error(f"Cover file may be too small.")
                    st.error(f"Error encoding FLAC file: {e}")
            elif selected_format == "wav":
                try:
                    output_path = f"output/{filename}.{encode_slider}.wav"
                    wav_encode(tempfile, payload_content, output_path, encode_slider)
                except Exception as e:
                    output_path = ""
                    st.error(f"Cover file may be too small.")
                    st.error(f"Error encoding WAV file: {e}")
            elif selected_format == "mkv":
                try:
                    output_path = f"output/{filename}.{encode_slider}.mkv"
                    mkv_encode(tempfile, output_path, payload_content, encode_slider)
                except Exception as e:
                    output_path = ""
                    st.error(f"Cover file may be too small.")
                    st.error(f"Error encoding MKV file: {e}")

    # Download Button
    with col2:
        if output_path != "":
            st.download_button("Download Encoded File",
                               data=open(output_path, 'rb').read(),
                               file_name=output_path,
                               key='download-single')

    return output_path, output


def encode_section_single_preview(cover_file, output, output_path):
    extension = cover_file.type.split('/')[-1]
    # Print Image below buttons
    if output_path != "":
        if extension in ["png", "jpg", "jpeg", "webp"]:
            col0, col1, col2, col3 = st.columns([1, 1, 1, 1])
            with col1:
                st.subheader("Original")
                st.image(cover_file, width=MAX_IMAGE_HEIGHT)
            with col2:
                st.subheader("Encoded")
                st.image(output, width=MAX_IMAGE_HEIGHT)
        elif extension in ["wav", "flac", "mp3"]:
            st.audio(output_path)
        elif extension in ['x-matroska']:
            st.write("MKV playback is unavailable.")

def encode_section_multi_encode(cover_file, payload_file, selected_format):

    # Move the pointer back to the start of the file so that we can read it again from the beginning
    payload_file.seek(0)
    payload_content = payload_file.read().decode('ascii', 'ignore')
    filename = cover_file.name.split('.')[0]
    extension = cover_file.type.split('/')[-1]

    # Convert file to selected format
    cover_file.seek(0)
    tempfile = convert_cover_to_selected_format(cover_file, selected_format)
    selected_format = selected_format.lower()

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
            if selected_format in ["png"]:
                for i in range(1, 9):
                    output = png_encode(tempfile, payload_content, i)
                    # png_encode will return bool during failure
                    if type(output) == bool:
                        st.error(f"{i} LSB is too small for this payload.")
                        continue
                    output_list.append(output)
                    # Save image to local storage to download the file
                    output_path = f"output/{filename}.{i}.png"
                    output.save(output_path)
                    output_paths.append(output_path)
            elif selected_format in ["jpg", "jpeg"]:
                for i in range(1, 9):
                    try:
                        output = encode_image(tempfile, payload_file, i)
                        output_list.append(output)
                        # Save image to local storage to download the file
                        output_path = f"output/{filename}.{i}.png"
                        output.save(output_path)
                    except Exception as e:
                        st.error(f"{i} LSB may be too small for this payload.")
                        st.error(f"Error: {e}")
            elif selected_format == "wav":
                for i in range(1, 9):
                    output_path = f"output/{filename}.{i}.wav"
                    # st.write("path done")
                    cover_file = io.BytesIO(cover_file.getvalue())  # Reset file stream for each loop iteration
                    try:
                        output_path = f"output/{filename}.{i}.wav"
                        output = wav_encode(tempfile, payload_content, output_path, i)
                        output_list.append(output)
                        output_paths.append(output_path)
                    except Exception as e:
                        st.error(f"{i} LSB may be too small for this payload.")
                        st.error(f"Error: {e}")
            elif selected_format == "flac":
                for i in range(1, 9):
                    try:
                        output_path = f"output/{filename}.{i}.flac"
                        output = flac_encode(tempfile, output_path, payload_content, i)
                        output_list.append(output)
                        output_paths.append(output_path)
                    except Exception as e:
                        st.error(f"{i} LSB may be too small for this payload.")
                        st.error(f"Error: {e}")
            elif selected_format == "mkv":
                for i in range(1, 9):
                    try:
                        st.write(f"Encoding LSB {i}")
                        output_path = f"output/{filename}.{i}.mkv"
                        mkv_encode(tempfile, output_path, payload_content, i)
                        output_paths.append(output_path)
                    except Exception as e:
                        st.error(f"{i} LSB may be too small for this payload.")
                        st.error(f"Error: {e}")

    # Download button
    with col2:
        # Different file types have different render steps
        if selected_format in ["png", "jpg", "jpeg", "wav", "flac", "x-matroska"]:
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

    return output_list, output_paths


def encode_section_multi_preview(cover_file, output_list, output_paths):
    extension = cover_file.type.split('/')[-1]

    # Create slider to switch between different images
    mult_encode_output_count = len(output_list)
    if mult_encode_output_count > 0:
        # Handle both images and WAV files in a row layout
        if extension in ["png", "jpg", "jpeg", "webp"]:
            cols = st.columns(mult_encode_output_count)
            for idx, col in enumerate(cols):
                with col:
                    st.write(f"{8 - mult_encode_output_count + 1 + idx} LSB")
                    st.image(output_list[idx], width=200)
        elif extension in ["wav", "flac"]:
            for idx in range(mult_encode_output_count):
                st.write(8 - mult_encode_output_count + 1 + idx)
                # For WAV files, plot and display the spectrogram
                spectrogram_image = plot_spectrogram(output_paths[idx])
                st.image(spectrogram_image, caption=f"Spectrogram {idx + 1}")
                st.audio(output_paths[idx])
        elif extension in ["x-matroska"]:
            st.write("In-browser playback not supported")
            st.write(f"Total files generated: {mult_encode_output_count}")


def encode_section():
    # Set the page configuration to use a wide layout
    st.set_page_config(layout="wide")

    # Set the title of the app
    st.title("Steganography Encoder/Decoder")

    st.markdown("## Encoding")

    cover_file, payload_file, selected_format = encode_section_choose_files()

    # Slider for selecting the number of LSB bits
    st.markdown("### LSB Bit Selection")
    encode_slider = st.slider("LSB bits used for encoding.", min_value=1, max_value=8, value=2, key='encode-slider')

    # Only show the button if there is already a cover_file and a payload_file
    if cover_file and payload_file:
        output_path, output = encode_section_single_encode(cover_file, payload_file, encode_slider, selected_format)
        encode_section_single_preview(cover_file, output, output_path)

        output_list, output_path = encode_section_multi_encode(cover_file, payload_file, selected_format)
        encode_section_multi_preview(cover_file, output_list, output_path)


def decode_section():
    st.markdown("## Decoding")

    # Use columns to make the layout cleaner
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Encoded File")
        encoded_file = st.file_uploader("Encoded file to use.", type=["png", 'webp',
                                                                      "wav", "flac",
                                                                      "mkv"], key="encoded_file")

    with col2:
        if encoded_file and encoded_file.type in ["png", "webp"]:
            st.image(encoded_file, width=MAX_IMAGE_HEIGHT)

    st.markdown("### LSB Bit Selection")
    decode_slider = st.slider("LSB bits used for encoding.", min_value=1, max_value=8, value=2, key='decode-slider')

    if encoded_file:
        if st.button("Decode File with selected LSB", key='decode-button'):
            extension = encoded_file.type.split('/')[1]

            if extension in ["png", "webp"]:
                decoded_content = png_decode(encoded_file, decode_slider)
                st.text_area("Complete File Content:", decoded_content, height=MAX_TEXT_HEIGHT, key="decode-text-area")

            elif extension == "wav":
                try:
                    decoded_content = wav_decode(encoded_file, decode_slider)
                    st.text_area("Complete File Content:", decoded_content, height=MAX_TEXT_HEIGHT, key="decode-text-area")
                except Exception as e:
                    st.write(f"Error decoding WAV file: {e}")

            elif extension == "flac":
                decoded_content = flac_decode(encoded_file, decode_slider)
                st.text_area("Complete File Content:", decoded_content, height=MAX_TEXT_HEIGHT, key="decode-text-area")

            elif extension == "x-matroska":
                mkv_path = create_temp_file(encoded_file)
                decoded_content = mkv_decode(mkv_path, decode_slider)
                st.text_area("Complete File Content:", decoded_content, height=MAX_TEXT_HEIGHT, key="decode-text-area")


        if st.button("Decode File (guess LSB)", key='decode-button-guess'):
            extension = encoded_file.type.split('/')[1]
            decoded_messages = {}  # To store results for each LSB level

            if extension == "png":
                try:
                    # Attempt decoding from 1 to 8 LSBs for PNG
                    for lsb in range(1, 9):
                        decoded_content = png_decode(encoded_file, lsb)
                        decoded_messages[lsb] = decoded_content
                    # Rank and display the results
                    ranked_messages = rank_decoded_messages(decoded_messages)
                    for bits, message, count in ranked_messages:
                        st.write(f"Decoded using {bits} LSBs (Alphanumeric Count: {count})")
                        st.text_area(f"Decoded Content (LSB {bits}):", message, height=MAX_TEXT_HEIGHT)
                except Exception as e:
                    st.write(f"Error decoding PNG file: {e}")

            elif extension == "wav":
                try:
                    # Attempt decoding from 1 to 8 LSBs for WAV
                    for lsb in range(1, 9):
                        decoded_content = wav_decode(encoded_file, lsb)
                        decoded_messages[lsb] = decoded_content
                        encoded_file = io.BytesIO(encoded_file.getvalue()) 
                    # Rank and display the results
                    ranked_messages = rank_decoded_messages(decoded_messages)
                    for bits, message, count in ranked_messages:
                        st.write(f"Decoded using {bits} LSBs (Alphanumeric Count: {count})")
                        st.text_area(f"Decoded Content (LSB {bits}):", message, height=MAX_TEXT_HEIGHT)
                except Exception as e:
                    st.write(f"Error decoding WAV file: {e}")

            elif extension == "flac":
                try:
                    # Attempt decoding from 1 to 8 LSBs for WAV
                    for lsb in range(1, 9):
                        decoded_content = flac_decode(encoded_file, lsb)
                        decoded_messages[lsb] = decoded_content
                        encoded_file = io.BytesIO(encoded_file.getvalue())
                        # Rank and display the results
                    ranked_messages = rank_decoded_messages(decoded_messages)
                    for bits, message, count in ranked_messages:
                        st.write(f"Decoded using {bits} LSBs (Alphanumeric Count: {count})")
                        st.text_area(f"Decoded Content (LSB {bits}):", message, height=MAX_TEXT_HEIGHT)
                except Exception as e:
                    st.write(f"Error decoding FLAC file: {e}")

            elif extension == "x-matroska":
                try:
                    # Attempt decoding from 1 to 8 LSBs for WAV
                    for lsb in range(1, 9):
                        mkv_path = create_temp_file(encoded_file)
                        decoded_content = mkv_decode(mkv_path, lsb)
                        decoded_messages[lsb] = decoded_content
                        encoded_file = io.BytesIO(encoded_file.getvalue())
                        # Rank and display the results
                    ranked_messages = rank_decoded_messages(decoded_messages)
                    for bits, message, count in ranked_messages:
                        st.write(f"Decoded using {bits} LSBs (Alphanumeric Count: {count})")
                        st.text_area(f"Decoded Content (LSB {bits}):", message, height=MAX_TEXT_HEIGHT)
                except Exception as e:
                    st.write(f"Error decoding FLAC file: {e}")


def rank_decoded_messages(decoded_messages):
    """Rank decoded messages based on the percentage of alphanumeric characters."""
    rankings = []
    
    for bits, message in decoded_messages.items():
        # Calculate total length and alphanumeric count
        total_length = len(message)
        alphanumeric_count = sum(c.isalnum() for c in message)

        # Calculate percentage, avoiding division by zero
        if total_length > 0:
            percentage = (alphanumeric_count / total_length) * 100
        else:
            percentage = 0
        
        rankings.append((bits, message, percentage))
    
    # Sort based on percentage (descending order)
    rankings = sorted(rankings, key=lambda x: x[2], reverse=True)
    
    return rankings
