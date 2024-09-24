import cv2
import numpy as np
import tempfile
import os
import subprocess

def list_ffmpeg_streams(video_path):
    command = f"ffmpeg -i {video_path} -hide_banner"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stderr.decode()
    print("FFmpeg stream information:")
    print(output)

def encode_video_with_cv2(video_file, text_file, output_path, lsb_bits=1):
    # Create a temporary file to store the uploaded video
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video_file:
        temp_video_file.write(video_file.read())  # Write the video bytes to a temp file
        temp_video_path = temp_video_file.name
    
    # List all streams in the video file (diagnostic step)
    list_ffmpeg_streams(temp_video_path)

    # Extract audio from the original video using FFmpeg
    audio_path = temp_video_path.replace('.mp4', '_audio.aac')
    extract_audio_command = f"ffmpeg -i {temp_video_path} -vn -acodec copy {audio_path} -y"
    
    result = subprocess.run(extract_audio_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"FFmpeg audio extraction failed: {result.stderr.decode()}")
        audio_path = None  # No audio extracted, set to None to skip audio merging
    else:
        print(f"Audio successfully extracted to {audio_path}")

    cap = cv2.VideoCapture(temp_video_path)
    
    if not cap.isOpened():
        print("Error: Could not open video.")
        return
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Load the text file and convert it to binary
    text_content = text_file.read().decode()  # Convert from byte to string
    text_bin = ''.join([format(ord(char), '08b') for char in text_content]) + '1' * lsb_bits  # End signal

    bits_per_frame = frame_width * frame_height * 3 * lsb_bits
    total_bits = len(text_bin)

    total_capacity = total_frames * bits_per_frame
    if total_bits > total_capacity:
        print("Error: Text file is too large to embed in this video.")
        return

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    data_index = 0
    data_len = len(text_bin)
    
    print("Starting video encoding...")

    for frame_idx in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break
        
        # Flatten the frame to access pixel values
        flat_frame = frame.flatten()

        # Embed the text binary data into the frame, up to the capacity of the frame
        for i in range(0, len(flat_frame)):
            if data_index < data_len:
                # Extract multiple bits from the text and embed them into the pixel
                bits_to_embed = text_bin[data_index:data_index + lsb_bits]
                if len(bits_to_embed) < lsb_bits:
                    bits_to_embed = bits_to_embed.ljust(lsb_bits, '0')
                
                # Embed bits in pixel's least significant bits
                flat_frame[i] = (flat_frame[i] & ~((1 << lsb_bits) - 1)) | int(bits_to_embed, 2)

                # Print encoded character and its byte only when a new character starts
                if data_index % (lsb_bits * 8) == 0:
                    char_index = data_index // (lsb_bits * 8)
                    if char_index < len(text_content):
                        char = text_content[char_index]
                        char_bin = format(ord(char), '08b')
                        print(f"Encoding character '{char}' with byte '{char_bin}' in frame {frame_idx + 1}/{total_frames}")

                data_index += lsb_bits
            else:
                break

        # Reshape the frame back and write it to the output video
        encoded_frame = flat_frame.reshape((frame_height, frame_width, 3))
        out.write(encoded_frame)

        # If data is fully embedded, continue to the next frame
        if data_index >= data_len:
            continue  # Continue to the next frame if data remains

    cap.release()
    out.release()

    if audio_path:
        final_output_path = output_path.replace('.mp4', '_with_audio.mp4')
        combine_audio_command = f"ffmpeg -i {output_path} -i {audio_path} -c copy {final_output_path} -y"
        result = subprocess.run(combine_audio_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            print(f"FFmpeg audio merging failed: {result.stderr.decode()}")
        else:
            print(f"Audio successfully merged into {final_output_path}")
    else:
        final_output_path = output_path
        print("No audio to merge with the final video.")

    try:
        os.remove(temp_video_path)
        if audio_path:
            os.remove(audio_path)
    except PermissionError:
        print(f"File {temp_video_path} is still in use, trying again later.")

    print(f"Encoding complete. Final video saved as {final_output_path}")
    return final_output_path
