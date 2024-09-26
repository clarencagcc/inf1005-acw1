import cv2
import random

def mkv_test(input_path, output_path):
    print("MKV Encoding")
    # Open video file
    cap = cv2.VideoCapture(input_path)

    # get video data
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    max_pixel = frame_count * width * height
    print("max pixel:", max_pixel)

    # Create a video writer to save the modified video using FFV1 (lossless)
    fourcc = cv2.VideoWriter_fourcc(*'FFV1')  # Use lossless FFV1 codec
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    curr_frame = 0
    while cap.isOpened():
        if curr_frame % 100 == 0:
            print(f"{curr_frame} of {frame_count}")

        curr_frame += 1
        ret, frame = cap.read()
        if not ret:
            break

        for i in range(height):
            for j in range(width):
                # Generate a random integer between 0 and 255
                blue = random.randint(0, 255)
                frame[i, j, 0] = blue

        # write to output file
        out.write(frame)

    cap.release()
    out.release()

    return True


if __name__ == "__main__":
    input_path = "input/comeon.mkv"
    output_path = "output/comeon_test.mkv"

    mkv_test(input_path, output_path)