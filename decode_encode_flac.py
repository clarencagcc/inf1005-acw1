import math

import soundfile as sf

message_delimiter = "\x00"

def get_text_from_file(path: str):
    try:
        with(open(path, 'r', encoding='utf-8')) as file:
            return file.read().encode('ascii', 'ignore').decode('ascii')
    except FileNotFoundError:
        return ""

def flac_encode(input_path, output_path, message, lsb_bits):
    # Read the FLAC file
    data, samplerate = sf.read(input_path, dtype='int16')

    # Flatten audio data to a 1D array
    flat_data = data.flatten()

    message += message_delimiter

    # Convert the message into a binary string
    binary_message = ''.join(format(ord(char), '08b') for char in message)

    # Track the number of bits encoded
    bits_encoded = 0
    total_bits = len(binary_message)

    # Amount of data needed to hide the stuff you want to hide
    data_needed = math.ceil(len(binary_message) / lsb_bits)
    if data_needed > len(flat_data):
        raise ValueError()

    # Modify the least significant bits in the audio data
    for i in range(len(flat_data)):
        if bits_encoded >= total_bits:
            break
        # Extract the current 'lsb_bits' from the message
        bits_to_encode = binary_message[bits_encoded: bits_encoded + lsb_bits]
        bits_to_encode_int = int(bits_to_encode, 2)

        # Clear the LSBs of the sample and then embed the new bits using binary OR
        flat_data[i] = (flat_data[i] & ~(2**lsb_bits - 1)) | bits_to_encode_int

        # Update the number of bits encoded
        bits_encoded += lsb_bits

    # Reshape the data back to its original shape
    reshaped_data = flat_data.reshape(data.shape)

    # Write the modified data to a new FLAC file
    sf.write(output_path, reshaped_data, samplerate)
    return True


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


def flac_decode(input_path, lsb_bits):
    # Read the FLAC file
    data, samplerate = sf.read(input_path, dtype='int16')

    # Flatten audio data to a 1D array
    flat_data = data.flatten()

    binary_message = ''
    bits_extracted = 0

    # Extract the least significant bits from the audio data
    for sample in flat_data:

        # Extract the 'lsb_bits' from the sample
        extracted_bits = sample & (2 ** lsb_bits - 1)

        # Convert the extracted bits to a binary string
        binary_message += f'{extracted_bits:0{lsb_bits}b}'

        # Keep track of how many bits have been extracted
        bits_extracted += lsb_bits

    # Convert the binary string into the hidden message
    decoded_message = bin_to_message(binary_message)

    return decoded_message


if __name__ == "__main__":
    # Example usage
    input_flac = 'input/ohdeer.flac'
    output_flac = 'output/ohdeer.flac'
    secret_message = get_text_from_file("payload/small.txt")

    # Embed the secret message
    flac_encode(input_flac, output_flac, secret_message, lsb_bits=8)

    # Example usage:
    message_length = 13  # Known length of the hidden message
    decoded_message = flac_decode(output_flac, lsb_bits=8)
    print(f"Decoded message: {decoded_message}")


