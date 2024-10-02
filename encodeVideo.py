import cv2
import os
from os.path import join
from moviepy.editor import VideoFileClip

message_delimiter = "\x00"  # End of message delimiter


def delete_file(input_path):
    # Delete the audio file
    try:
        os.remove(input_path)
        print(f"Temporary file {input_path} deleted successfully.")
    except OSError as e:
        print(f"Unable to delete {input_path}. Error: {e}")
        pass

def message_to_bin(message: str):
    """Convert a string to binary using utf-8 encoding."""
    return ''.join(format(byte, '08b') for byte in message.encode('utf-8'))

def bin_to_message(binary_data):
    """Convert binary data back to a UTF-8 string."""
    byte_chunks = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    byte_array = bytearray([int(byte, 2) for byte in byte_chunks])
    return byte_array.decode('utf-8', errors='ignore')

def convert_to_lossless_format(video_file, output_format="AVI"):
    """
    Converts the input video file to the specified lossless format (AVI with FFV1, MOV with Apple Animation or FFV1).
    """
    temp_dir = "temp_frames_lossless"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Open the input video file with OpenCV
    video_capture = cv2.VideoCapture(video_file)
    if not video_capture.isOpened():
        raise Exception(f"Failed to open the video file {video_file}")

    frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video_capture.get(cv2.CAP_PROP_FPS)

    # Conversion to AVI using FFV1 codec
    if output_format == "AVI":
        fourcc = cv2.VideoWriter_fourcc(*'FFV1')  # FFV1 codec for lossless AVI
        output_file = join(temp_dir, "lossless_video.avi")
        video_writer = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))

        for frame_num in range(frame_count):
            ret, frame = video_capture.read()
            if not ret:
                break
            video_writer.write(frame)

        video_capture.release()
        video_writer.release()
        return output_file

    # Conversion to MOV using Apple Animation codec
    elif output_format == "MOV":
        fourcc = cv2.VideoWriter_fourcc(*'png ')  # Apple Animation codec for MOV
        output_file = join(temp_dir, "lossless_video.mov")
        video_writer = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))

        for frame_num in range(frame_count):
            ret, frame = video_capture.read()
            if not ret:
                break
            video_writer.write(frame)

        video_capture.release()
        video_writer.release()
        return output_file

    else:
        raise ValueError(f"Unsupported lossless format: {output_format}")

def embed_text_in_frame(frame, binary_message, payload_index, lsb_bits):
    """
    Embed as much of the binary message into the frame as possible.
    Returns the updated frame and new payload index.
    """
    height, width, _ = frame.shape
    total_bits = len(binary_message)
    bit_index = payload_index  # Start from the current payload index

    for row in range(height):
        for col in range(width):
            if bit_index < total_bits:
                # Get the bits that we will be appending to the current binary value
                bits_to_encode = binary_message[bit_index: bit_index + lsb_bits]
                if len(bits_to_encode) < lsb_bits:
                    bits_to_encode = bits_to_encode.ljust(lsb_bits, '0')

                # Modify the blue channel's LSBs to store the message
                green = frame[row, col, 1]
                green_binary = format(green, '08b')
                green_binary = green_binary[:-lsb_bits] + bits_to_encode
                frame[row, col, 1] = int(green_binary, 2)

                # Print the binary being encoded
                # if bit_index % 8 == 0:
                #     char_being_encoded = bin_to_message(binary_message[bit_index: bit_index + 8])
                #     print(f"Embedding '{char_being_encoded}' in frame pixel ({row}, {col})")

                bit_index += lsb_bits
            else:
                # Once the message is fully embedded, return the updated frame and new payload index
                return frame, bit_index

    return frame, bit_index

def encode_video_with_cv2(video_file, text_file, output_path, lsb_bits=1, selected_format="AVI"):
    """
    Encode a message into the video by modifying the pixel values using the LSB technique.
    Prints the character being embedded in each frame during the embedding process.
    Handles both ASCII and non-ASCII characters.
    """
    # Read the text payload (supports non-ASCII characters with UTF-8 encoding)
    with open(text_file, 'r', encoding="utf-8") as f:
        payload = f.read() + message_delimiter  # Add the delimiter at the end of the message

    binary_message = message_to_bin(payload)  # Convert the message to binary
    payload_index = 0  # Start embedding from the first bit of the binary message
    binary_message_len = len(binary_message)

    # Convert video to selected lossless format
    lossless_path = convert_to_lossless_format(video_file, output_format=selected_format)

    # Open the video file
    video_capture = cv2.VideoCapture(lossless_path)
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))

    # Create a video writer to save the modified video
    fourcc = cv2.VideoWriter_fourcc(*'FFV1') if selected_format == "AVI" else cv2.VideoWriter_fourcc(*'png ')
    output_file = f"{output_path}.{selected_format.lower()}"
    video_writer = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

    while video_capture.isOpened() and payload_index < binary_message_len:
        ret, frame = video_capture.read()
        if not ret:
            break

        # Embed as much of the message as possible into the frame
        frame, payload_index = embed_text_in_frame(frame, binary_message, payload_index, lsb_bits)

        # Write the modified frame to the output video
        video_writer.write(frame)

        if payload_index >= binary_message_len:
            print(f"Message fully embedded after {frame_count} frames.")
            break

    video_capture.release()
    video_writer.release()

    # Now, add audio back to the video using MoviePy
    try:
        original_clip = VideoFileClip(video_file)
        if original_clip.audio:
            print("Adding audio back to the encoded video...")
            encoded_clip = VideoFileClip(output_file)
            video_with_audio = encoded_clip.set_audio(original_clip.audio)
            final_output_path = f"{output_path}_with_audio.{selected_format.lower()}"
            video_with_audio.write_videofile(final_output_path, codec="ffv1" if selected_format == "AVI" else "png", preset="ultrafast")
            return final_output_path
        else:
            print("No audio found in the original video.")
    except Exception as e:
        print(f"Error adding audio or writing video: {e}")

    print("Encoding completed.")

    return output_file

def avi_encode(video_file, payload_content, output_path, lsb_bits=1):
    """
    Converts the video to a lossless format (AVI or MOV) and embeds text into the video frames using LSB steganography.
    """

    binary_message = message_to_bin(payload_content)  # Convert the message to binary
    binary_message_len = len(binary_message)
    payload_index = 0  # Start embedding from the first bit of the binary message

    # Open the video file
    cap = cv2.VideoCapture(video_file)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Create a video writer to save the modified video
    fourcc = cv2.VideoWriter_fourcc(*'FFV1')
    soundless_video_path = output_path.replace(".avi", "_temp.avi")
    out = cv2.VideoWriter(soundless_video_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if payload_index < binary_message_len:
            # Embed as much of the message as possible into the frame
            frame, payload_index = embed_text_in_frame(frame, binary_message, payload_index, lsb_bits)

        # Write the modified frame to the output video
        out.write(frame)

    cap.release()
    out.release()

    # Now, add audio back to the video using MoviePy
    try:
        original_clip = VideoFileClip(video_file)
        if original_clip.audio:
            print("Adding audio back to the encoded video...")
            encoded_clip = VideoFileClip(soundless_video_path)
            video_with_audio = encoded_clip.set_audio(original_clip.audio)
            video_with_audio.write_videofile(output_path, codec="ffv1", preset="ultrafast")
            return output_path
        else:
            print("No audio found in the original video.")
    except Exception as e:
        print(f"Error adding audio or writing video: {e}")

    print("Encoding completed.")

    delete_file(soundless_video_path)

    return output_path


def mov_encode(video_file, payload_content, output_path, lsb_bits=1):
    """
    Converts the video to a lossless format (MOV) and embeds text into the video frames using LSB steganography.
    """

    binary_message = message_to_bin(payload_content)  # Convert the message to binary
    binary_message_len = len(binary_message)
    payload_index = 0  # Start embedding from the first bit of the binary message

    # Open the video file
    cap = cv2.VideoCapture(video_file)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Create a video writer to save the modified video
    fourcc = cv2.VideoWriter_fourcc(*'FFV1')
    soundless_video_path = output_path.replace(".mov", "_temp.mov")
    out = cv2.VideoWriter(soundless_video_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if payload_index < binary_message_len:
            # Embed as much of the message as possible into the frame
            frame, payload_index = embed_text_in_frame(frame, binary_message, payload_index, lsb_bits)

        # Write the modified frame to the output video
        out.write(frame)

    cap.release()
    out.release()

    # Now, add audio back to the video using MoviePy
    try:
        original_clip = VideoFileClip(video_file)
        if original_clip.audio:
            print("Adding audio back to the encoded video...")
            encoded_clip = VideoFileClip(soundless_video_path)
            video_with_audio = encoded_clip.set_audio(original_clip.audio)
            video_with_audio.write_videofile(output_path, codec="ffv1", preset="ultrafast")
            return output_path
        else:
            print("No audio found in the original video.")
    except Exception as e:
        print(f"Error adding audio or writing video: {e}")

    print("Encoding completed.")

    delete_file(soundless_video_path)

    return output_path
