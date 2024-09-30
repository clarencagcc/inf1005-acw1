import cv2
import numpy as np
from pydub import AudioSegment

def encode_audio_to_video(video_path, audio_path, output_path):
    # Load the cover video
    video = cv2.VideoCapture(video_path)
    
    # Get video properties
    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Load the audio to be hidden
    audio = AudioSegment.from_file(audio_path)
    audio_data = np.array(audio.get_array_of_samples())
    
    # Convert audio data to binary
    audio_binary = ''.join(format(i, '016b') for i in audio_data)
    
    # Prepare the output video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_index = 0
    audio_index = 0
    
    while True:
        ret, frame = video.read()
        if not ret:
            break
        
        # Flatten the frame
        flat_frame = frame.flatten()
        
        # Encode audio data into the frame
        for i in range(len(flat_frame)):
            if audio_index < len(audio_binary):
                flat_frame[i] = (flat_frame[i] & 0xFE) | int(audio_binary[audio_index])
                audio_index += 1
            else:
                break
        
        # Reshape the frame and write to output
        encoded_frame = flat_frame.reshape((height, width, 3))
        out.write(encoded_frame.astype(np.uint8))
        
        frame_index += 1
        
        if audio_index >= len(audio_binary):
            break
    
    video.release()
    out.release()

def decode_audio_from_video(video_path, output_path):
    # Load the encoded video
    video = cv2.VideoCapture(video_path)
    
    audio_binary = ""
    
    while True:
        ret, frame = video.read()
        if not ret:
            break
        
        # Flatten the frame
        flat_frame = frame.flatten()
        
        # Extract the least significant bit from each byte
        frame_bits = ''.join(str(i & 1) for i in flat_frame)
        audio_binary += frame_bits
    
    video.release()
    
    # Convert binary back to audio samples
    audio_data = [int(audio_binary[i:i+16], 2) for i in range(0, len(audio_binary), 16)]
    
    # Create an AudioSegment from the samples
    audio = AudioSegment(
        audio_data,
        frame_rate=44100,
        sample_width=2,
        channels=1
    )
    
    # Export the audio file
    audio.export(output_path, format="wav")
