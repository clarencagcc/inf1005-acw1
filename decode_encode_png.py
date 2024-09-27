import math

from PIL import Image

message_delimiter = "\x00"

def get_text_from_file(path: str):
    try:
        with(open(path, 'r', encoding='utf-8')) as file:
            return file.read().encode('ascii', 'ignore').decode('ascii')
    except FileNotFoundError:
        return ""

def message_to_bin(message: str):
    """Convert a string to binary."""
    return ''.join(format(ord(c), '08b') for c in message)

def png_encode(image_path: str, message: str, lsb_bits=1):
    """Encodes a message into the PNG image."""
    image = Image.open(image_path)
    # image must be in RGB mode  may not be in RGB
    image = image.convert('RGBA')

    message += message_delimiter  # Use ### as a delimiter for the end of the message
    binary_message = message_to_bin(message)
    binary_message_len = len(binary_message)

    # Limits bits to update to only 8
    if lsb_bits > 8:
        lsb_bits = 8

    pixels = image.getdata()
    # Check if we have enough bytes to hide the message
    bytes_needed = math.ceil(len(binary_message) / lsb_bits)
    if bytes_needed > len(image.getdata()) * 3:
        raise ValueError("Cover file does not have enough data.")

    message_index = 0
    new_pixels = []
    for pixel in pixels:
        if message_index < binary_message_len:
            new_pixel = list(pixel)

            # Replace the least significant bit of the red, green, or blue channel with message bits
            for i in range(3):  # Loop through RGB channels
                if message_index < binary_message_len:
                    bits_to_encode = binary_message[message_index: message_index + lsb_bits]
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

                    message_index += lsb_bits

            new_pixels.append(tuple(new_pixel))
        else:
            new_pixels.append(pixel)

    # Save the modified image
    encoded_image = Image.new(image.mode, image.size)
    encoded_image.putdata(new_pixels)
    return encoded_image

def bin_to_message(binary_data: str):
    """Convert binary string back to text."""
    message = []
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i + 8]
        char = chr(int(byte, 2))
        message.append(char)
        if char == message_delimiter:
            break
    return ''.join(message).rstrip(message_delimiter)

def png_decode(image_path: str, bits=1):
    """Extract the hidden message from the PNG image."""
    image = Image.open(image_path)
    image = image.convert('RGBA')

    binary_message = ""
    for pixel in image.getdata():
        for i in range(3):  # Extract from RGB channels
            # Extract the least significant 'bits' from the pixel value using binary operations
            bits_value = pixel[i] & (2 ** bits - 1)
            binary_message += format(bits_value, f'0{bits}b')

    hidden_message = bin_to_message(binary_message)
    return hidden_message


