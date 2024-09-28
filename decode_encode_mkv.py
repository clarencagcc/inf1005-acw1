import cv2
import math
import subprocess

from common import msg_to_bin, bin_to_msg, process_payload
from common import delim_check
from common import get_text_from_file, delete_file

def mkv_encode(input_path, output_path, message, lsb_bits=1):
    print(f"\nEncoding to {output_path}")
    # Extract audio file from original video file using ffmpeg
    # We'll save the audio as a temp file which we'll delete after all is said and done
    temp_audio_path = "input/temp.aac"
    command = f"ffmpeg -y -i {input_path} -vn -acodec copy {temp_audio_path}"
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    soundless_video_path = output_path.replace(".mkv", "_temp.mkv")

    # Open video file
    cap = cv2.VideoCapture(input_path)

    message = process_payload(message)
    print(f"message {message[:100]}")
    binary_message = msg_to_bin(message)
    binary_message_len = len(binary_message)
    payload_index = 0

    # get video data
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    max_pixel = frame_count * width * height

    # Create a video writer to save the modified video using FFV1 (lossless)
    fourcc = cv2.VideoWriter_fourcc(*'FFV1')  # Use lossless FFV1 codec
    out = cv2.VideoWriter(soundless_video_path, fourcc, fps, (width, height))

    bytes_needed = math.ceil(len(binary_message) / lsb_bits)
    if bytes_needed > frame_count * width * height:
        raise ValueError("Cover file does not have enough data.")

    pixel_count = 1
    pixel_edited_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        for i in range(height):
            for j in range(width):
                pixel_count += 1
                # Leave the loop if we have oth
                if payload_index < binary_message_len:
                    # Get the bits that we will be appending to the current binary value
                    bits_to_encode = binary_message[payload_index: payload_index + lsb_bits]
                    # If there are not enough characters in the binary, we just add some zeroes to the left
                    if len(bits_to_encode) < lsb_bits:
                        bits_to_encode = bits_to_encode.ljust(lsb_bits, '0')

                    # Get pixel val of binary
                    blue = frame[i, j, 0]

                    # get the binary data of the original pixel based on the size of the data we are encoding
                    # if we are replacing all 8 bits, then we just need to set the value to the provided bits
                    if lsb_bits == 8:
                        blue = int(bits_to_encode, 2)
                    else:
                        blue_binary = format(blue, '08b')
                        blue_binary = blue_binary[:-lsb_bits] + bits_to_encode
                        blue = int(blue_binary, 2)

                    frame[i, j, 0] = blue

                    payload_index += lsb_bits
                    pixel_edited_count += 1

        # write to output file
        out.write(frame)

    cap.release()
    out.release()

    # Combine audio with video
    command = f"ffmpeg -y -i {soundless_video_path} -i {temp_audio_path} -c:v copy -c:a aac {output_path}"
    #command = f"ffmpeg -y -i {soundless_video_path} -c:v copy -c:a aac {output_path}"
    #subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(command, shell=True)
    # delete the temp files
    delete_file(temp_audio_path)
    delete_file(soundless_video_path)

    print(f"Pixels Edited: {pixel_edited_count}/{pixel_count}")
    print("MKV Encoding End\b")
    return True

def mkv_decode(input_path, lsb_bits=1):
    cap = cv2.VideoCapture(input_path)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    binary_message = []
    done = False

    curr_pixel = 0
    max_pixel = frame_count * width * height
    while cap.isOpened() and not done:
        ret, frame = cap.read()

        if not ret:
            break

        height, width, _ = frame.shape
        for i in range(height):
            if done:
                break

            for j in range(width):
                # Get the blue channel value
                blue = frame[i, j, 0]
                # Extract the least significant 'bits' from the pixel value using binary operations
                bits_value = blue & (2 ** lsb_bits - 1)

                binary_value = format(bits_value, f'0{lsb_bits}b')
                binary_message.extend(binary_value)

                # Check if we've encountered the message delimiter
                if delim_check(binary_message):
                    done = True
                    break

                curr_pixel += 1
                if curr_pixel % 1000000 == 0:
                    print(f"{curr_pixel} of {max_pixel}")

    cap.release()
    # Convert the binary message to readable text
    final_message = bin_to_msg(binary_message)

    return final_message


if __name__ == "__main__":
    input_path = "input/comeon.mkv"
    output_path = "output/comeon.mkv"
    payload_path = "payload/02_smallplus.txt"
    message = get_text_from_file(payload_path)

    mkv_encode(input_path, output_path, message, lsb_bits=8)

    decoded = mkv_decode(output_path, lsb_bits=8)
    #print(decoded)


