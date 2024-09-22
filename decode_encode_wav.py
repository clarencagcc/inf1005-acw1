import wave
import numpy as np

def text_to_bin(text):
    """Convert a string into its binary representation."""
    return ''.join([format(ord(i), '08b') for i in text])

def wav_encode(audio_file, message, output_file, bit_depth):
    with wave.open(audio_file, 'rb') as audio:
        params = audio.getparams()
        frames = bytearray(list(audio.readframes(audio.getnframes())))

        # Convert the message to binary and append the delimiter
        message_bin = text_to_bin(message) + '1111111111111110'
        message_len = len(message_bin)

        # Total available bits to modify in the audio file
        total_available_bits = len(frames) * bit_depth

        if message_len > total_available_bits:
            raise ValueError("Message is too large to embed in the audio file with the selected bit depth.")

        # Embed the message into the least significant bits
        bit_idx = 0
        for frame_idx in range(len(frames)):
            current_frame = frames[frame_idx]
            for bit_pos in range(bit_depth):
                if bit_idx < message_len:
                    # Clear the bit at the position bit_pos and insert the message bit
                    mask = ~(1 << bit_pos)  # Clear bit at bit_pos
                    current_frame = (current_frame & mask) | (int(message_bin[bit_idx]) << bit_pos)
                    bit_idx += 1
                else:
                    break
            frames[frame_idx] = current_frame

        # Save the modified frames to the output file
        with wave.open(output_file, 'wb') as modified_audio:
            modified_audio.setparams(params)
            modified_audio.writeframes(bytes(frames))

# Decode

def bin_to_text(binary):
    """Convert binary string to ASCII text."""
    message = ''.join([chr(int(binary[i:i+8], 2)) for i in range(0, len(binary), 8)])
    return message

def wav_decode(audio_file, bit_depth):
    """Extract a hidden message from a WAV audio file using specified bits per sample."""
    if bit_depth < 1 or bit_depth > 8:
        raise ValueError("bit_depth must be between 1 and 8")

    # Open the audio file
    with wave.open(audio_file, 'rb') as audio:
        frames = bytearray(list(audio.readframes(audio.getnframes())))

        # Extract the bits from each frame based on the bit depth
        bits = []
        for frame in frames:
            for bit_pos in range(bit_depth):
                bits.append(str((frame >> bit_pos) & 1))  # Extract each of the LSBs based on bit depth

        # Combine all bits into a single string
        bits = ''.join(bits)

        # Look for the end delimiter ('1111111111111110')
        end_index = bits.find('1111111111111110')
        if end_index != -1:
            message_bits = bits[:end_index]
            message = bin_to_text(message_bits)
            return message