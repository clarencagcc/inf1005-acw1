from stegano import lsb
import cv2
import os
import numpy as np
from os.path import join
from PIL import Image
from moviepy.editor import VideoFileClip, ImageSequenceClip

def convert_to_lossless_format(video_file, output_format="AVI"):
    """
    Converts the input video file to the specified lossless format (AVI with FFV1, MOV with Apple Animation or FFV1).
    """
    temp_dir = "temp_frames_lossless"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Open the input video file with OpenCV
    video_capture = cv2.VideoCapture(video_file)
    if not video_capture.isOpened():
        raise Exception(f"Failed to open the video file {video_file}")

    frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video_capture.get(cv2.CAP_PROP_FPS)

    # Conversion to AVI using FFV1 codec
    if output_format == "AVI":
        fourcc = cv2.VideoWriter_fourcc(*'FFV1')  # FFV1 codec for lossless AVI
        output_file = join(temp_dir, "lossless_video.avi")
        video_writer = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))

        for frame_num in range(frame_count):
            ret, frame = video_capture.read()
            if not ret:
                break
            video_writer.write(frame)  # Write frame directly to the AVI file

        video_capture.release()
        video_writer.release()
        return output_file  # Return the path to the AVI file

    # Conversion to MOV using Apple Animation codec (or FFV1 if desired)
    elif output_format == "MOV":
        fourcc = cv2.VideoWriter_fourcc(*'png ')  # Apple Animation codec for MOV
        output_file = join(temp_dir, "lossless_video.mov")
        video_writer = cv2.VideoWriter(output_file, fourcc, fps, (frame_width, frame_height))

        for frame_num in range(frame_count):
            ret, frame = video_capture.read()
            if not ret:
                break
            video_writer.write(frame)  # Write frame directly to the MOV file

        video_capture.release()
        video_writer.release()
        return output_file  # Return the path to the MOV file

    else:
        raise ValueError(f"Unsupported lossless format: {output_format}")


def encode_video_with_cv2(video_file, text_file, output_path, lsb_bits=1, selected_format="AVI"):
    """
    Converts the video to a lossless format (AVI or MOV) and embeds text into the video frames using LSB steganography.
    """
    # Convert the video to the selected lossless format
    print(f"Converting {video_file} to lossless {selected_format} format...")
    lossless_path = convert_to_lossless_format(video_file, output_format=selected_format)

    # Open the converted video (AVI or MOV) and extract frames
    video_capture = cv2.VideoCapture(lossless_path)
    frames = []
    fps = video_capture.get(cv2.CAP_PROP_FPS)

    # Read the text payload with utf-8 encoding
    with open(text_file, 'r', encoding="utf-8") as f:
        payload = f.read()

    text_index = 0
    total_chars = len(payload)

    frame_num = 0
    while video_capture.isOpened():
        ret, frame = video_capture.read()
        if not ret:
            break

        # Convert the frame to PIL format for embedding
        frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if text_index < total_chars:
            text_segment = payload[text_index:text_index + lsb_bits]
            text_index += lsb_bits
            print(f"Embedding '{text_segment}' into frame {frame_num}")

            try:
                encoded_frame_pil = lsb.hide(frame_pil, text_segment)
                encoded_frame = np.array(encoded_frame_pil)
                frame = cv2.cvtColor(encoded_frame, cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"Error encoding frame {frame_num}: {e}")
                break

        # Append the modified frame to the frame list
        frames.append(frame)
        frame_num += 1

    video_capture.release()

    # Create a final video using MoviePy from the processed frames and add audio back
    try:
        video_clip = ImageSequenceClip([cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in frames], fps=fps)
        original_clip = VideoFileClip(video_file)

        if original_clip.audio:
            print("Adding audio back to the encoded video...")
            video_with_audio = video_clip.set_audio(original_clip.audio)
            final_output_path = f"{output_path}_with_audio.{selected_format.lower()}"
            video_with_audio.write_videofile(final_output_path, codec="ffv1" if selected_format == "AVI" else "png", preset="ultrafast")
            return final_output_path
        else:
            print("No audio found in the original video.")
    except Exception as e:
        print(f"Error adding audio or writing video: {e}")

    # If no audio, write the final video without audio
    final_output_path = f"{output_path}.{selected_format.lower()}"
    video_clip.write_videofile(final_output_path, codec="ffv1" if selected_format == "AVI" else "png", preset="ultrafast")
    return final_output_path


def avi_encode(video_file, text_file, output_path, lsb_bits=1):
    """
    Converts the video to a lossless format (AVI or MOV) and embeds text into the video frames using LSB steganography.
    """

    # Open the converted video (AVI or MOV) and extract frames
    video_capture = cv2.VideoCapture(video_file)
    frames = []
    fps = video_capture.get(cv2.CAP_PROP_FPS)

    # Read the text payload with utf-8 encoding
    text_file.seek(0)
    payload = text_file.read().decode('utf-8', 'ignore') + '\x00'

    text_index = 0
    total_chars = len(payload)

    frame_num = 0
    while video_capture.isOpened():
        ret, frame = video_capture.read()
        if not ret:
            break

        # Convert the frame to PIL format for embedding
        frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if text_index < total_chars:
            print(f"{text_index}/{total_chars}")
            text_segment = payload[text_index:text_index + lsb_bits]
            text_index += lsb_bits
            print(f"Embedding '{text_segment}' into frame {frame_num}")

            try:
                encoded_frame_pil = lsb.hide(frame_pil, text_segment)
                encoded_frame = np.array(encoded_frame_pil)
                frame = cv2.cvtColor(encoded_frame, cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"Error encoding frame {frame_num}: {e}")
                break

        # Append the modified frame to the frame list
        frames.append(frame)
        frame_num += 1

    video_capture.release()

    # Create a final video using MoviePy from the processed frames and add audio back
    video_clip = ImageSequenceClip([cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in frames], fps=fps)
    original_clip = VideoFileClip(video_file)

    if original_clip.audio:
        print("Adding audio back to the encoded video...")
        video_with_audio = video_clip.set_audio(original_clip.audio)
        video_with_audio.write_videofile(output_path, codec="ffv1", preset="ultrafast")
        return output_path
    else:
        print("No audio found in the original video.")

    # If no audio, write the final video without audio
    final_output_path = f"{output_path}.avi"
    video_clip.write_videofile(final_output_path, codec="ffv1", preset="ultrafast")
    return final_output_path


def mov_encode(video_file, text_file, output_path, lsb_bits=1):
    """
    Converts the video to a lossless format (MOV) and embeds text into the video frames using LSB steganography.
    """

    # Open the converted video (MOV) and extract frames
    video_capture = cv2.VideoCapture(video_file)
    frames = []
    fps = video_capture.get(cv2.CAP_PROP_FPS)

    # Read the text payload with utf-8 encoding
    text_file.seek(0)
    payload = text_file.read().decode('utf-8', 'ignore') + '\x00'

    text_index = 0
    total_chars = len(payload)

    frame_num = 0
    while video_capture.isOpened():
        ret, frame = video_capture.read()
        if not ret:
            break

        # Convert the frame to PIL format for embedding
        frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if text_index < total_chars:
            text_segment = payload[text_index:text_index + lsb_bits]
            text_index += lsb_bits
            print(f"Embedding '{text_segment}' into frame {frame_num}")

            try:
                encoded_frame_pil = lsb.hide(frame_pil, text_segment)
                encoded_frame = np.array(encoded_frame_pil)
                frame = cv2.cvtColor(encoded_frame, cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"Error encoding frame {frame_num}: {e}")
                break

        # Append the modified frame to the frame list
        frames.append(frame)
        frame_num += 1

    video_capture.release()

    # Create a final video using MoviePy from the processed frames and add audio back
    try:
        video_clip = ImageSequenceClip([cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in frames], fps=fps)
        original_clip = VideoFileClip(video_file)

        if original_clip.audio:
            print("Adding audio back to the encoded video...")
            video_with_audio = video_clip.set_audio(original_clip.audio)
            video_with_audio.write_videofile(output_path, codec="png", preset="ultrafast")
            return output_path
        else:
            print("No audio found in the original video.")
    except Exception as e:
        print(f"Error adding audio or writing video: {e}")

    # If no audio, write the final video without audio
    video_clip.write_videofile(output_path, codec="png", preset="ultrafast")
    return output_path
