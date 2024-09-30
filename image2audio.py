import numpy as np
from PIL import Image
from pydub import AudioSegment
import io
import wave

def encode_image_to_audio(audio_file, image_file, output_path):
    try:
        # Load the cover audio
        cover_audio = AudioSegment.from_file(audio_file)
        audio_data = np.array(cover_audio.get_array_of_samples())

        # Load the image to be hidden
        image = Image.open(image_file)
        image_array = np.array(image)
        
        # Flatten the image array and convert to binary
        flat_image = image_array.flatten()
        image_binary = ''.join(format(i, '08b') for i in flat_image)

        # Encode the image dimensions and mode at the beginning
        width, height = image.size
        mode = image.mode
        header = f"{format(width, '016b')},{format(height, '016b')},{mode}"
        header_binary = ''.join(format(ord(c), '08b') for c in header)

        # Combine header and image data
        binary_data = header_binary + '0' * 8 + image_binary  # '\0' as a separator

        # Ensure the image data can fit in the audio
        if len(binary_data) > len(audio_data):
            raise ValueError("Image is too large for this audio file")

        # Modify the least significant bit of each audio sample
        for i, bit in enumerate(binary_data):
            if i < len(audio_data):
                audio_data[i] = (audio_data[i] & ~1) | int(bit)

        # Create a new AudioSegment from the modified samples
        encoded_audio = AudioSegment(
            audio_data.tobytes(),
            frame_rate=cover_audio.frame_rate,
            sample_width=cover_audio.sample_width,
            channels=cover_audio.channels
        )

        # Export the encoded audio file
        encoded_audio.export(output_path, format="wav")
        
        print(f"Image encoded into audio and saved to {output_path}")
        return encoded_audio

    except Exception as e:
        print(f"Error encoding image to audio: {str(e)}")
        return None

def decode_image_from_audio(audio_file, output_path):
    try:
        # Load the audio file
        audio = AudioSegment.from_file(audio_file)
        
        # Convert audio to raw data
        raw_data = np.array(audio.get_array_of_samples())
        
        # Extract the binary data from the least significant bit
        binary_data = ''.join(str(sample & 1) for sample in raw_data)
        
        # Find the separator (assuming we used '\0' as a separator)
        separator_index = binary_data.find('0' * 8)
        if separator_index == -1:
            raise ValueError("Image data separator not found")
        
        # Extract the header information
        header = binary_data[:separator_index]
        image_data = binary_data[separator_index + 8:]  # Skip the separator
        
        # Decode the header
        header_parts = header.split(',')
        if len(header_parts) != 3:
            raise ValueError(f"Invalid header format. Expected 3 parts, got {len(header_parts)}")
        
        width = int(header_parts[0], 2)
        height = int(header_parts[1], 2)
        mode = ''.join(chr(int(header_parts[2][i:i+8], 2)) for i in range(0, len(header_parts[2]), 8))
        
        print(f"Decoded header: width={width}, height={height}, mode={mode}")
        
        # Convert binary image data to bytes
        image_bytes = bytes(int(image_data[i:i+8], 2) for i in range(0, width * height * len(mode) * 8, 8))
        
        # Create the image
        image = Image.frombytes(mode, (width, height), image_bytes)
        
        # Save the image
        image.save(output_path)
        
        print(f"Decoded image saved to {output_path}")
        return image
    
    except Exception as e:
        print(f"Error decoding image from audio: {str(e)}")
        return None