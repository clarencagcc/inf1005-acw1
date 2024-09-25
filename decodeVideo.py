import cv2
import os
import shutil
from PIL import Image
from stegano import lsb
from moviepy.editor import VideoFileClip
from os.path import join

def decode_video_with_cv2(video_file, lsb_bits=1, input_format="AVI"):
    """
    Decodes a video or PNG sequence to extract the hidden text using LSB steganography.
    Supports AVI and MOV formats by processing the video frame by frame to handle large file sizes efficiently.
    """
    temp_dir = "temp_frames_decode"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Handle PNG Sequence
    if input_format == "PNG Sequence":
        frame_directory = f"{video_file}_frames"
        if not os.path.exists(frame_directory):
            raise FileNotFoundError(f"The directory {frame_directory} was not found.")
        
        # Get all PNG files in the directory and process them
        frame_paths = sorted([join(frame_directory, f) for f in os.listdir(frame_directory) if f.endswith(".png")])
        if not frame_paths:
            raise FileNotFoundError("No frames found in the specified PNG sequence directory.")
        print(f"Decoding text from {len(frame_paths)} PNG frames...")

    # Use MoviePy for decoding MOV files (Apple Animation codec)
    elif input_format == "MOV":
        print(f"Decoding MOV video {video_file} using MoviePy...")

        # Open the MOV video with MoviePy
        try:
            video_clip = VideoFileClip(video_file)
            frame_count = int(video_clip.fps * video_clip.duration)
            frame_paths = []
            
            # Process each frame and save them temporarily as PNG
            for frame_num in range(frame_count):
                frame = video_clip.get_frame(frame_num / video_clip.fps)
                frame_path = join(temp_dir, f"frame_{frame_num:05d}.png")
                Image.fromarray(frame).save(frame_path)
                frame_paths.append(frame_path)

            video_clip.reader.close()
        except Exception as e:
            raise Exception(f"Failed to decode MOV video: {e}")

        if not frame_paths:
            raise FileNotFoundError("No frames extracted from the MOV video.")

    # For AVI and other video formats that OpenCV supports (unchanged logic)
    else:
        video_capture = cv2.VideoCapture(video_file)
        if not video_capture.isOpened():
            raise Exception(f"Failed to open the video file {video_file}")
        
        frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_paths = []

        print(f"Decoding text from {frame_count} frames of video...")

        frame_num = 0
        while video_capture.isOpened():
            ret, frame = video_capture.read()
            if not ret:
                break

            frame_path = join(temp_dir, f"frame_{frame_num:05d}.png")
            cv2.imwrite(frame_path, frame)
            frame_paths.append(frame_path)
            frame_num += 1

        video_capture.release()

        if not frame_paths:
            raise FileNotFoundError("No frames extracted from the video.")

    # Initialize variable to store the decoded message
    decoded_message = ""

    # Process each frame to reveal hidden text using Stegano LSB
    for frame_num, frame_path in enumerate(frame_paths):
        try:
            if not os.path.exists(frame_path):
                print(f"Frame {frame_num} does not exist. Skipping this frame.")
                continue

            frame_pil = Image.open(frame_path)
            hidden_message = lsb.reveal(frame_pil)  # Use Stegano LSB to reveal the hidden message

            if hidden_message:
                decoded_message += hidden_message
                print(f"Decoded from frame {frame_num}: {hidden_message}")
            else:
                print(f"No more hidden message found, stopping decoding at frame {frame_num}.")
                break
        except Exception as e:
            print(f"Error decoding frame {frame_num}: {e}")
            break

    # Clean up the temporary directory if we extracted frames from a video
    shutil.rmtree(temp_dir)

    if decoded_message:
        print(f"Decoded Message: {decoded_message}")
    else:
        print("No message was decoded.")

    return decoded_message
