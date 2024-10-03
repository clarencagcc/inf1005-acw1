import math

import streamlit as st
import zipfile
import os
import io
import tempfile

from decode_encode_png import png_decode, png_encode
from decode_encode_wav import wav_decode, wav_encode
from decode_encode_wav_payload import WAVPayload, isWavPayload
from decode_encode_png_payload import PNGPayload, isPngPayload
from decode_encode_flac import flac_decode, flac_encode
from decode_encode_mkv import mkv_encode, mkv_decode
from encodeVideo import avi_encode, mov_encode
from decodeVideo import decode_video_with_cv2
from encoder import encode_image
from audio_spectrogram import plot_spectrogram

from PIL import Image
from pydub import AudioSegment
import moviepy.editor as mp

MAX_IMAGE_HEIGHT = 400
MAX_TEXT_HEIGHT = 400

def create_temp_file(file, extension):
    # Create a temporary file with a unique path
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
        file.seek(0)
        # Write the uploaded file's content to the temporary file
        temp_file.write(file.read())
        temp_file_path = temp_file.name
        return temp_file_path


def create_temp_text_file(text: str):
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='ascii', suffix='.txt')

    # Write the string to the temporary file
    temp_file.write(text)

    # Save the file name and close the file
    temp_file_path = temp_file.name
    temp_file.close()

    return temp_file

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

            elif cover_file.type in ["audio/mpeg"]:
                mp3_audio = AudioSegment.from_mp3(cover_file)
                mp3_audio.export(output_path, format=selected_format)

            # Handle video conversion
            elif cover_file.type in ["video/x-matroska", "video/avi", "application/octet-stream", "video/mp4", "video/quicktime"]:
                video_codec = "libx264"

                tempfile_path = create_temp_file(cover_file, selected_format)
                clip = mp.VideoFileClip(tempfile_path)
                clip.write_videofile(output_path, codec=video_codec, audio_codec="aac", preset="ultrafast")

            return output_path
        except Exception as e:
            st.error(f"convert_cover_to_selected_format() Error: {e}")
            return None


def convert_to_mp4(filepath):
    try:
        # Create a temporary file to store the output
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_output:
            output_path = temp_output.name  # Get the name of the temporary file

        # Load the video file using MoviePy
        clip = mp.VideoFileClip(filepath)

        # Write the video to the output path in MP4 format
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="ultrafast")

        # Clean up and close the clip
        clip.close()

        return output_path
    except Exception as e:
        print(f"Error converting file to MP4: {e}")
        return None

def encode_section_choose_files():
    # Use columns to make the layout cleaner
    col1, col2 = st.columns(2)
    output_format = []
    selected_format = None

    # File uploader for Payload
    with col1:
        st.subheader("Payload")
        payload_file = st.file_uploader("Drag and drop file here", type=["txt", "wav", "png"], key="payload")

        if payload_file:
            if payload_file.type in ["text/plain"]:
                # Encode and decode because some characters (like em dash) aren't in the ascii table
                payload_content = payload_file.read().decode('ascii', 'ignore')
                st.text_area("Complete File Content:", payload_content, height=MAX_TEXT_HEIGHT)
            elif payload_file.type in ["audio/wav"]:
                WavData = WAVPayload.readFromPath(payload_file)
                payload_content = WavData.convertToPayload()
                st.text_area("Complete File Content:", payload_content, height=25)
                st.audio(payload_file)
            elif payload_file.type in ["image/png"]:
                PngData = PNGPayload.readFromPath(payload_file)
                payload_content = PngData.convertToPayload()
                st.text_area("Complete File Content:", payload_content, height=25)
                st.image(payload_file)

    # File uploader for Cover
    with col2:
        st.subheader("Cover")
        cover_file = st.file_uploader("Drag and drop file here", type=["jpg", "png", "jpeg", 'webp',
                                                                       "wav", "flac", "mp3",
                                                                       "mkv", 'avi', 'mov', "mp4"], key="cover")

        if cover_file:
            if cover_file.type in ["image/jpg", "image/png", "image/jpeg", "image/webp"]:
                output_format = ['PNG']
                st.image(cover_file, width=MAX_IMAGE_HEIGHT)

            elif cover_file.type in ["audio/wav", "audio/flac", "audio/mpeg"]:
                output_format = ['FLAC', 'WAV']
                spectrogram_image = plot_spectrogram(cover_file)
                st.image(spectrogram_image, caption=f"Spectrogram")
                st.audio(cover_file)

            elif cover_file.type in ["video/x-matroska", "video/avi", "application/octet-stream", "video/mp4", "video/quicktime"]:
                output_format = ['MKV', "AVI", "MOV"]  # Lossless formats for encoding
                preview_file = convert_cover_to_selected_format(cover_file, "mp4")
                st.video(preview_file)

            selected_format = st.selectbox("Select the output format", output_format)

    return cover_file, payload_file, selected_format


def encode_section_single_encode(cover_file, payload_file, encode_slider, selected_format):
    col1, col2 = st.columns(2)

    # Move the pointer back to the start of the file so that we can read it again from the beginning
    payload_file.seek(0)
    payload_content = ""

    if payload_file.type in ["text/plain"]:
        # Encode and decode because some characters (like em dash) aren't in the ascii table
        payload_content = payload_file.read().decode('ascii', 'ignore')
    elif payload_file.type in ["audio/wav"]:
        WavData = WAVPayload.readFromPath(payload_file)
        payload_content = WavData.convertToPayload()
    elif payload_file.type in ["image/png"]:
        PNGData = PNGPayload.readFromPath(payload_file)
        payload_content = PNGData.convertToPayload()
    temp_text_file = create_temp_text_file(payload_content)
    filename = cover_file.name.split('.')[0]

    output_path = ""
    output = None

    # Encode Button
    with col1:
        #st.write(extension)
        if st.button("Encode using selected LSB", key="encode-button"):
            with st.spinner("Encoding..."):
                # Convert file to selected format
                cover_file.seek(0)
                tempfile = convert_cover_to_selected_format(cover_file, selected_format)
                selected_format = selected_format.lower()
                try:
                    if selected_format in ["png", "webp"]:
                        output = png_encode(tempfile, payload_content, encode_slider)
                        # Save image to local storage to download the file
                        output_path = f"output/{filename}.{encode_slider}.{selected_format}"
                        output.save(output_path, loseless=True)
                    elif selected_format in ["jpg", "jpeg"]:
                        output = encode_image(tempfile, temp_text_file, encode_slider)
                        # Save image to local storage to download the file
                        output_path = f"output/{filename}.{encode_slider}.png"
                        output.save(output_path)
                    elif selected_format in "flac":
                        output_path = f"output/{filename}.{encode_slider}.flac"
                        flac_encode(tempfile, output_path, payload_content, encode_slider)
                    elif selected_format == "wav":
                        output_path = f"output/{filename}.{encode_slider}.wav"
                        wav_encode(tempfile, payload_content, output_path, encode_slider)
                    elif selected_format == "mkv":
                        output_path = f"output/{filename}.{encode_slider}.mkv"
                        mkv_encode(tempfile, output_path, payload_content, encode_slider)
                    elif selected_format == "avi":
                        output_path = f"output/{filename}.{encode_slider}.avi"
                        avi_encode(tempfile, payload_content, output_path, encode_slider)
                    elif selected_format == "mov":
                        output_path = f"output/{filename}.{encode_slider}.mov"
                        mov_encode(tempfile, payload_content, output_path, encode_slider)
                except Exception as e:
                    output_path = ""
                    st.error(f"Error encoding {selected_format} file: {e}")

    # Download Button
    with col2:
        if output_path != "":
            st.download_button("Download Encoded File",
                               data=open(output_path, 'rb').read(),
                               file_name=output_path,
                               key='download-single')

    return output_path, output


def encode_section_single_preview(cover_file, output, output_path, selected_format):
    selected_format = selected_format.lower()
    if output_path != "":
        if selected_format in ["png"]:
            col0, col1, col2, col3 = st.columns([1, 1, 1, 1])
            with col1:
                st.subheader("Original")
                st.image(cover_file, width=MAX_IMAGE_HEIGHT)
            with col2:
                st.subheader("Encoded")
                st.image(output, width=MAX_IMAGE_HEIGHT)
        elif selected_format in ["wav", "flac"]:
            st.audio(output_path)
        elif selected_format in ['mkv', 'avi', 'mov']:
            mp4_preview = convert_to_mp4(output_path)
            st.video(mp4_preview)


def encode_section_multi_encode(cover_file, payload_file, selected_format):

    # Move the pointer back to the start of the file so that we can read it again from the beginning
    payload_file.seek(0)
    payload_content = ""
    if payload_file.type in ["text/plain"]:
        # Encode and decode because some characters (like em dash) aren't in the ascii table
        payload_content = payload_file.read().decode('ascii', 'ignore')
    elif payload_file.type in ["audio/wav"]:
        WavData = WAVPayload.readFromPath(payload_file)
        payload_content = WavData.convertToPayload()
    elif payload_file.type in ["image/png"]:
        PNGData = PNGPayload.readFromPath(payload_file)
        payload_content = PNGData.convertToPayload()
    temp_text_file = create_temp_text_file(payload_content)
    filename = cover_file.name.split('.')[0]

    # Buttons for downloading multiple encoded files
    col1, col2 = st.columns(2)

    output_list = []
    output_paths = []

    # Encode Button
    with col1:
        # Button to encode from 1 LSB to 8 LSB
        if st.button("Encode from 1 LSB to 8 LSB", key="encode-multi"):
            with st.spinner("Encoding..."):
                # Convert file to selected format
                cover_file.seek(0)
                tempfile = convert_cover_to_selected_format(cover_file, selected_format)
                selected_format = selected_format.lower()

                for i in range(1, 9):
                    # Encode the file for each LSB
                    # Save all those generated files to output folder
                    # store paths for each file
                    # Use those paths to generate slideshow
                    try:
                        if selected_format in ["png"]:
                            output = png_encode(tempfile, payload_content, i)
                            # png_encode will return bool during failure
                            output_list.append(output)
                            # Save image to local storage to download the file
                            output_path = f"output/{filename}.{i}.png"
                            output.save(output_path)
                            output_paths.append(output_path)
                        elif selected_format in ["jpg", "jpeg"]:
                            output = encode_image(tempfile, temp_text_file, i)
                            output_list.append(output)
                            # Save image to local storage to download the file
                            output_path = f"output/{filename}.{i}.png"
                            output.save(output_path)
                        elif selected_format == "wav":
                            # st.write("path done")
                            cover_file = io.BytesIO(cover_file.getvalue())  # Reset file stream for each loop iteration
                            output_path = f"output/{filename}.{i}.wav"
                            output = wav_encode(tempfile, payload_content, output_path, i)
                            output_list.append(output)
                            output_paths.append(output_path)
                        elif selected_format == "flac":
                            output_path = f"output/{filename}.{i}.flac"
                            output = flac_encode(tempfile, output_path, payload_content, i)
                            output_list.append(output)
                            output_paths.append(output_path)
                        elif selected_format == "mkv":
                            output_path = f"output/{filename}.{i}.mkv"
                            output = mkv_encode(tempfile, output_path, payload_content, i)
                            output_paths.append(output_path)
                            output_list.append(output)
                        elif selected_format == "avi":
                            output_path = f"output/{filename}.{i}.avi"
                            output = avi_encode(tempfile, payload_content, output_path, i)
                            output_paths.append(output_path)
                            output_list.append(output)
                        elif selected_format == "mov":
                            output_path = f"output/{filename}.{i}.mov"
                            output = mov_encode(tempfile, payload_content, output_path, i)
                            output_paths.append(output_path)
                            output_list.append(output)
                    except Exception as e:
                        st.error(f"Error encoding {selected_format} file: {e}")

    # Download button
    with col2:
        # Different file types have different render steps
        if selected_format in ["png", "jpg", "jpeg", "wav", "flac", "mkv", 'avi', 'mov']:
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


def encode_section_multi_preview(cover_file, output_list, output_paths, selected_format):
    selected_format = selected_format.lower()
    # Create slider to switch between different images
    mult_encode_output_count = len(output_paths)
    if mult_encode_output_count > 0:
        # Handle both images and WAV files in a row layout
        if selected_format in ["png"]:
            col_count = 2
            row_count = math.ceil(mult_encode_output_count / col_count)
            output_idx = 0
            for i in range(0, row_count):
                cols = st.columns(col_count)
                for col in cols:
                    with col:
                        if output_idx >= mult_encode_output_count:
                            break
                        st.write(f"{8 - mult_encode_output_count + 1 + output_idx} LSB")
                        st.image(output_list[output_idx], width=MAX_IMAGE_HEIGHT)
                        output_idx += 1
        elif selected_format in ["wav", "flac"]:
            for idx in range(mult_encode_output_count):
                st.write(8 - mult_encode_output_count + 1 + idx)
                # For WAV files, plot and display the spectrogram
                spectrogram_image = plot_spectrogram(output_paths[idx])
                st.image(spectrogram_image, caption=f"Spectrogram {idx + 1}")
                st.audio(output_paths[idx])
        elif selected_format in ["mkv", 'avi', 'mov']:
            col_count = 2
            row_count = math.ceil(mult_encode_output_count / col_count)
            output_idx = 0
            for i in range(0, row_count):
                cols = st.columns(col_count)
                for col in cols:
                    with col:
                        if output_idx >= mult_encode_output_count:
                            break
                        st.write(f"{8 - mult_encode_output_count + 1 + output_idx} LSB")
                        mp4_preview = convert_to_mp4(output_paths[output_idx])
                        st.video(mp4_preview)
                        output_idx += 1


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
        encode_section_single_preview(cover_file, output, output_path, selected_format)

        output_list, output_path = encode_section_multi_encode(cover_file, payload_file, selected_format)
        encode_section_multi_preview(cover_file, output_list, output_path, selected_format)


def decode_section():
    st.markdown("## Decoding")

    # Use columns to make the layout cleaner
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Encoded File")
        encoded_file = st.file_uploader("Encoded file to use.", type=["png", 'webp',
                                                                      "wav", "flac",
                                                                      "mkv", "avi", 'mov'], key="encoded_file")

    with col2:
        if encoded_file and encoded_file.type in ["png", "webp"]:
            st.image(encoded_file, width=MAX_IMAGE_HEIGHT)

    st.markdown("### LSB Bit Selection")
    decode_slider = st.slider("LSB bits used for encoding.", min_value=1, max_value=8, value=2, key='decode-slider')

    if encoded_file:
        if st.button("Decode File with selected LSB", key='decode-button'):
            extension = encoded_file.type.split('/')[1]

            with st.spinner("Decoding..."):
                try:
                    if extension in ["png", "webp"]:
                        decoded_content = png_decode(encoded_file, decode_slider)

                    elif extension == "wav":
                        decoded_content = wav_decode(encoded_file, decode_slider)

                    elif extension == "flac":
                        decoded_content = flac_decode(encoded_file, decode_slider)

                    elif extension == "x-matroska":
                        mkv_path = create_temp_file(encoded_file, "mkv")
                        decoded_content = mkv_decode(mkv_path, decode_slider)

                    elif extension == "avi":
                        file_path = create_temp_file(encoded_file, "avi")
                        decoded_content = decode_video_with_cv2(file_path, decode_slider, "AVI")

                    elif extension == "octet-stream":
                        file_path = create_temp_file(encoded_file, "mov")
                        decoded_content = decode_video_with_cv2(file_path, decode_slider, "MOV")
                except Exception as e:
                            st.write(f"Error decoding {extension} file: {e}")

                if isWavPayload(decoded_content):
                    decoded_wav_path = f"output/{encoded_file.name[:-4]}_decoded.wav"
                    WAVPayload.readFromString(decoded_content, decoded_wav_path)
                    st.audio(decoded_wav_path)
                    st.download_button("Download Decoded WAV",
                                       data=open(decoded_wav_path, 'rb').read(),
                                       file_name=decoded_wav_path,
                                       key='download-decoded-wav')

                if isPngPayload(decoded_content):
                    decoded_img_path = f"output/{encoded_file.name[:-4]}_decoded.png"
                    PNGPayload.readFromString(decoded_content, decoded_img_path)
                    st.image(decoded_img_path)
                    st.download_button("Download Decoded WAV",
                                       data=open(decoded_img_path, 'rb').read(),
                                       file_name=decoded_img_path,
                                       key='download-decoded-img')

                st.text_area("Complete File Content:", decoded_content, height=25, key="decode-text-area")

        if st.button("Decode File (guess LSB)", key='decode-button-guess'):

            with st.spinner("Decoding..."):
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
                        st.error(f"Error decoding PNG file: {e}")

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
                        st.error(f"Error decoding WAV file: {e}")

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
                        st.error(f"Error decoding FLAC file: {e}")

                elif extension == "x-matroska":
                    try:
                        # Attempt decoding from 1 to 8 LSBs for WAV
                        for lsb in range(1, 9):
                            mkv_path = create_temp_file(encoded_file, "mkv")
                            decoded_content = mkv_decode(mkv_path, lsb)
                            decoded_messages[lsb] = decoded_content
                            encoded_file = io.BytesIO(encoded_file.getvalue())
                            # Rank and display the results
                        ranked_messages = rank_decoded_messages(decoded_messages)
                        for bits, message, count in ranked_messages:
                            st.write(f"Decoded using {bits} LSBs (Alphanumeric Count: {count})")
                            st.text_area(f"Decoded Content (LSB {bits}):", message, height=MAX_TEXT_HEIGHT)
                    except Exception as e:
                        st.error(f"Error decoding MKV file: {e}")

                elif extension == "avi":
                    try:
                        # Attempt decoding from 1 to 8 LSBs for WAV
                        for lsb in range(1, 9):
                            avi_path = create_temp_file(encoded_file, "avi")
                            decoded_content = decode_video_with_cv2(file_path, decode_slider, "AVI")
                            decoded_messages[lsb] = decoded_content
                            encoded_file = io.BytesIO(encoded_file.getvalue())
                            # Rank and display the results
                        ranked_messages = rank_decoded_messages(decoded_messages)
                        for bits, message, count in ranked_messages:
                            st.write(f"Decoded using {bits} LSBs (Alphanumeric Count: {count})")
                            st.text_area(f"Decoded Content (LSB {bits}):", message, height=MAX_TEXT_HEIGHT)
                    except Exception as e:
                        st.error(f"Error decoding AVI file: {e}")

                elif extension == "octet-stream":
                    try:
                        # Attempt decoding from 1 to 8 LSBs for WAV
                        for lsb in range(1, 9):
                            avi_path = create_temp_file(encoded_file, "mov")
                            decoded_content = decode_video_with_cv2(file_path, decode_slider, "MOV")
                            decoded_messages[lsb] = decoded_content
                            encoded_file = io.BytesIO(encoded_file.getvalue())
                            # Rank and display the results
                        ranked_messages = rank_decoded_messages(decoded_messages)
                        for bits, message, count in ranked_messages:
                            st.write(f"Decoded using {bits} LSBs (Alphanumeric Count: {count})")
                            st.text_area(f"Decoded Content (LSB {bits}):", message, height=MAX_TEXT_HEIGHT)
                    except Exception as e:
                        st.error(f"Error decoding AVI file: {e}")


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
