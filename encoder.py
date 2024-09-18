# encoder.py
from PIL import Image
import numpy as np

def text_to_bin(text):
    return ''.join(format(ord(c), '08b') for c in text)

def encode_image(image_file, text_file, lsb_bits):
    # getting image and the pixels in the uploaded image
    # coverting pixels to a numpy array for easier manipulation
    image = Image.open(image_file)
    pixels = np.array(image)

    # Ensure the image is in RGB mode
    if pixels.ndim != 3 or pixels.shape[2] != 3:
        raise ValueError("The image must be in RGB mode.")

    # Read the text file and convert to binary
    text = text_file.read().decode('utf-8')
    text_bin = text_to_bin(text)

    # calulating the total no. of pixels (divide by 3 because each pixel has 3 channels i.e RGB)
    total_pixels = pixels.size // 3  # Total number of pixels
    if len(text_bin) > total_pixels * lsb_bits:
        # making sure that there are enough pixels to encode text considering the no. of LSB bits
        raise ValueError("The text file is too large to encode in this image with the chosen LSB bits.")

    # Create the mask for clearing LSB bits
    # used to zero out the bits where the text will be encoded
    mask = (1 << lsb_bits) - 1

    # Encode the binary text into the image
    index = 0
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            pixel = list(pixels[i, j]) # iterating over each pixel in the image
            

            # for each color channel, prepares to modify pixel value
            # clear_mask is computed to zero out bits where text will be embedded
            for k in range(3):  # R, G, B channels
                if index < len(text_bin):
                    # Create the mask to clear the LSB bits
                    clear_mask = ~mask & 0xFF  # Ensure mask is within uint8 range
                    # New LSB value, extracts the next segment of the binary text to be hidden
                    new_lsb = int(text_bin[index:index + lsb_bits], 2)
                    
                    # Update pixel value
                    pixel[k] = (pixel[k] & clear_mask) | new_lsb
                    # need this to ensure pixel value remains within the valid range
                    # will spit out errors otherwise idk y
                    pixel[k] = np.clip(pixel[k], 0, 255)
                    index += lsb_bits
                
                if index >= len(text_bin):
                    break
            pixels[i, j] = tuple(pixel)
            
            if index >= len(text_bin):
                break
        if index >= len(text_bin):
            break

    # Convert numpy array back to PIL image
    # and return encoded image
    encoded_img = Image.fromarray(pixels)
    return encoded_img