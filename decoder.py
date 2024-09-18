# encoder.py
from PIL import Image
import numpy as np

def decode_image(image_file, lsb_bits):
    # Open the image and convert to NumPy array
    image = Image.open(image_file)
    pixels = np.array(image)

    # Ensure the image is in RGB mode
    if pixels.ndim != 3 or pixels.shape[2] != 3:
        raise ValueError("The image must be in RGB mode.")

    # Create the mask to extract LSB bits
    mask = (1 << lsb_bits) - 1

    # Extract binary data from the image
    binary_data = ''
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            pixel = pixels[i, j]
            for k in range(3):  # R, G, B channels
                # Extract LSB bits
                lsb = pixel[k] & mask
                binary_data += format(lsb, '0' + str(lsb_bits) + 'b')

    # Convert binary string to text
    message = ''
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i + 8]
        if len(byte) < 8:
            break  # Incomplete byte
        char = chr(int(byte, 2))
        if char == '\x00':  # Null byte used as a delimiter
            break
        message += char

    return message
