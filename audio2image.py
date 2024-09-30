import numpy as np
from PIL import Image
from pydub import AudioSegment
import io
import wave

import numpy as np
from PIL import Image
from pydub import AudioSegment
import io

def encode_audio_to_image(image_file, audio_file, output_path):
    # Load the cover image
    cover = Image.open(image_file)
    cover_array = np.array(cover)

    # Load the audio file
    try:
        # First, try to read the audio file using wave
        with io.BytesIO(audio_file.read()) as audio_bytes:
            with wave.open(audio_bytes, 'rb') as wav_file:
                n_channels, sampwidth, framerate, n_frames, _, _ = wav_file.getparams()
                audio_data = np.frombuffer(wav_file.readframes(n_frames), dtype=np.int16)
    except (wave.Error, EOFError):
        # If wave.open fails, try using pydub
        audio_file.seek(0)  # Reset file pointer
        audio = AudioSegment.from_file(audio_file, format="wav")
        audio_data = np.array(audio.get_array_of_samples())

    # Flatten the image array
    flat_cover = cover_array.flatten()

    # Ensure the audio data can fit in the image
    if len(audio_data) * 16 > len(flat_cover):
        raise ValueError("Audio file is too large for this image")

    # Convert audio data to binary
    audio_binary = ''.join(format(i & 0xFFFF, '016b') for i in audio_data)

    # Encode the audio length at the beginning
    audio_len = format(len(audio_data), '032b')
    binary_data = audio_len + audio_binary

    # Modify the least significant bit of each color channel
    for i, bit in enumerate(binary_data):
        if i < len(flat_cover):
            flat_cover[i] = (flat_cover[i] & 0xFE) | int(bit)

    # Reshape the array back to the original image shape
    encoded_array = flat_cover.reshape(cover_array.shape)

    # Create the encoded image
    encoded_image = Image.fromarray(encoded_array.astype('uint8'), cover.mode)

    # Save the encoded image
    encoded_image.save(output_path)

    # Return the encoded image object
    return encoded_image

def decode_audio_from_image(image_file, output_path):
    try:
        # Load the encoded image
        encoded_image = Image.open(image_file)
        encoded_array = np.array(encoded_image)

        # Flatten the image array
        flat_encoded = encoded_array.flatten()

        # Extract the binary data
        binary_data = ''.join(str(i & 1) for i in flat_encoded)

        # Extract the audio length
        audio_len = int(binary_data[:32], 2)

        # Extract the audio data
        audio_binary = binary_data[32:32 + audio_len * 16]

        # Convert binary back to audio samples
        audio_data = [int(audio_binary[i:i+16], 2) for i in range(0, len(audio_binary), 16)]

        # Ensure we have at least one audio sample
        if not audio_data:
            raise ValueError("No audio data found in the image")

        # Create a WAV file from the samples
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(44100)  # Standard sample rate
            wav_file.writeframes(np.array(audio_data, dtype=np.int16).tobytes())

        print(f"Decoded audio saved to {output_path}")
        return output_path

    except Exception as e:
        print(f"Error decoding audio from image: {str(e)}")
        return None