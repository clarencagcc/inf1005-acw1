import cv2
import os
import shutil
from PIL import Image

message_delimiter = "\x00"  # End of message delimiter


def bin_to_message(binary_data):
    """
    Converts binary data into a human-readable message.
    Stops converting once the message delimiter is found.
    """
    message = ''
    for i in range(0, len(binary_data), 8):
        byte = "".join(binary_data[i:i + 8])
        char = chr(int(byte, 2))
        message += char
        if char == message_delimiter:
            break
    return message


def decode_video_with_cv2(video_file, lsb_bits=1, input_format="AVI"):
    """
    Decodes a video to extract the hidden text using LSB steganography.
    Handles lossless video formats like AVI (FFV1) or MOV (Apple Animation).
    """
    temp_dir = "temp_frames_decode"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Open the video capture if the input is a video file (e.g., AVI with FFV1)
    video_capture = cv2.VideoCapture(video_file)
    if not video_capture.isOpened():
        raise Exception(f"Failed to open the video file {video_file}")

    frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    max_pixel = frame_count * width * height

    print(f"Total Pixel Count = {max_pixel}")
    print(f"Decoding text from {frame_count} frames of video...")

    binary_message = []
    delimiter_found = False

    # Process each frame one by one to extract hidden text
    for frame_num in range(frame_count):
        ret, frame = video_capture.read()
        if not ret:
            break

        # Iterate over the pixels in the frame
        for row in range(height):
            for col in range(width):

                green = frame[row, col, 1]
                # Extract the least significant 'bits' from the pixel value using binary operations
                bits_value = green & (2 ** lsb_bits - 1)

                binary_value = format(bits_value, f'0{lsb_bits}b')
                binary_message.extend(binary_value)

                # Check if we've encountered the message delimiter
                if ''.join(binary_message[-len(message_to_bin(message_delimiter)):]) == message_to_bin(message_delimiter):
                    delimiter_found = True
                    break

            if delimiter_found:
                print(f"No more hidden message found, stopping decoding at frame {frame_num}.")
                break

        if delimiter_found:
            break

    video_capture.release()

    # Convert binary message to readable text
    binary_message = ''.join(binary_message)
    decoded_message = ''.join([chr(int(binary_message[i:i + 8], 2)) for i in range(0, len(binary_message), 8)])

    # Return the decoded message up to the delimiter
    decoded_message = decoded_message.split(message_delimiter)[0]

    # Clean up temporary files if any
    shutil.rmtree(temp_dir)

    if decoded_message:
        print(f"Message Decoded...")
        print(f"Snippet: {decoded_message[:100]}")
    else:
        print("No message was decoded.")

    return decoded_message


def message_to_bin(message: str):
    """Convert a string to binary using utf-8 encoding."""
    return ''.join(format(ord(c), '08b') for c in message)


# Example usage:
if __name__ == "__main__":
    video_file = "output_video_with_audio.mov"  # Your video file path here
    lsb_bits = 2  # Example LSB bits used during encoding (set as per your encoding)
    
    decoded_message = decode_video_with_cv2(video_file, lsb_bits=lsb_bits, input_format="MOV")
    print("Decoded Message:", decoded_message)
