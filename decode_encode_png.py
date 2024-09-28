import math
from PIL import Image

from common import msg_to_bin, bin_to_msg, process_payload
from common import delim_check

def png_encode(image_path: str, message: str, lsb_bits=1):
    """Encodes a message into the PNG image."""
    image = Image.open(image_path)
    # image must be in RGB mode  may not be in RGB
    image = image.convert('RGBA')

    # Preprocess payload before insertion
    message = process_payload(message)
    binary_message = msg_to_bin(message)
    binary_message_len = len(binary_message)
    payload_index = 0

    # Limits bits to update to only 8
    if lsb_bits > 8:
        lsb_bits = 8

    pixels = image.getdata()
    # Check if we have enough bytes to hide the message
    bytes_needed = math.ceil(len(binary_message) / lsb_bits)
    if bytes_needed > len(image.getdata()) * 3:
        raise ValueError("Cover file does not have enough data.")

    new_pixels = []
    for pixel in pixels:
        if payload_index < binary_message_len:
            new_pixel = list(pixel)

            # Replace the least significant bit of the red, green, or blue channel with message bits
            for i in range(3):  # Loop through RGB channels
                if payload_index < binary_message_len:
                    bits_to_encode = binary_message[payload_index: payload_index + lsb_bits]
                    # If there are not enough characters in the binary
                    # add 0s from the left
                    if len(bits_to_encode) < lsb_bits:
                        bits_to_encode = bits_to_encode.ljust(lsb_bits, '0')

                    # get the binary data of the original pixel based on the size of the data we are encoding
                    if lsb_bits == 8:
                        new_pixel[i] = int(bits_to_encode, 2)
                    else:
                        # get pixel in 8 bit binary
                        pixel_value_binary = format(new_pixel[i], '08b')
                        pixel_value_binary = pixel_value_binary[:-lsb_bits] + bits_to_encode
                        # convert updated string back to int
                        new_pixel[i] = int(pixel_value_binary, 2)

                    payload_index += lsb_bits

            new_pixels.append(tuple(new_pixel))
        else:
            new_pixels.append(pixel)

    # Save the modified image
    encoded_image = Image.new(image.mode, image.size)
    encoded_image.putdata(new_pixels)
    return encoded_image


def png_decode(image_path: str, bits=1):
    """Extract the hidden message from the PNG image."""
    image = Image.open(image_path)
    image = image.convert('RGBA')

    binary_message = []
    done = False
    for pixel in image.getdata():
        if done:
            break

        for i in range(3):  # Extract from RGB channels
            # Extract the least significant 'bits' from the pixel value using binary operations
            bits_value = pixel[i] & (2 ** bits - 1)
            binary_value = format(bits_value, f'0{bits}b')
            binary_message.extend(binary_value)

            if delim_check(binary_message):
                done = True
                break

    hidden_message = bin_to_msg(binary_message)
    return hidden_message


