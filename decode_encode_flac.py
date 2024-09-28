import math

import soundfile as sf

from common import msg_to_bin, bin_to_msg, process_payload
from common import delim_check
from common import get_text_from_file

def flac_encode(input_path, output_path, message, lsb_bits):
    # Read the FLAC file
    data, samplerate = sf.read(input_path, dtype='int16')

    message = process_payload(message)
    binary_message = msg_to_bin(message)
    binary_message_len = len(binary_message)
    payload_idx = 0

    # Flatten audio data to a 1D array
    flat_data = data.flatten()

    # Amount of data needed to hide the stuff you want to hide
    data_needed = math.ceil(len(binary_message) / lsb_bits)
    if data_needed > len(flat_data):
        raise ValueError("Cover file does not have enough data.")

    # Modify the least significant bits in the audio data
    for i in range(len(flat_data)):
        if payload_idx >= binary_message_len:
            break
        # Extract the current 'lsb_bits' from the message
        bits_to_encode = binary_message[payload_idx: payload_idx + lsb_bits]
        bits_to_encode_int = int(bits_to_encode, 2)

        # Clear the LSBs of the sample and then embed the new bits using binary OR
        flat_data[i] = (flat_data[i] & ~(2**lsb_bits - 1)) | bits_to_encode_int

        # Update the number of bits encoded
        payload_idx += lsb_bits

    # Reshape the data back to its original shape
    reshaped_data = flat_data.reshape(data.shape)

    # Write the modified data to a new FLAC file
    sf.write(output_path, reshaped_data, samplerate)
    return True

def flac_decode(input_path, lsb_bits):
    # Read the FLAC file
    data, samplerate = sf.read(input_path, dtype='int16')

    # Flatten audio data to a 1D array
    flat_data = data.flatten()

    binary_message = []

    # Extract the least significant bits from the audio data
    for sample in flat_data:
        # Extract the 'lsb_bits' from the sample
        bits_value = sample & (2 ** lsb_bits - 1)

        binary_value = format(bits_value, f'0{lsb_bits}b')
        binary_message.extend(binary_value)

        if delim_check(binary_message):
            break

    final_message = bin_to_msg(binary_message)
    return final_message


if __name__ == "__main__":
    # Example usage
    input_flac = 'input/ohdeer.flac'
    output_flac = 'output/ohdeer.flac'
    secret_message = get_text_from_file("payload/02_smallplus.txt")

    # Embed the secret message
    flac_encode(input_flac, output_flac, secret_message, lsb_bits=8)

    # Example usage:
    message_length = 13  # Known length of the hidden message
    decoded_message = flac_decode(output_flac, lsb_bits=8)
    print(f"Decoded message: {decoded_message}")


