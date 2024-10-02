from PIL import Image
import io
from decode_encode_png import png_encode, png_decode
from decode_encode_wav import wav_encode, wav_decode
from decode_encode_mkv import mkv_encode, mkv_decode

def isPngPayload(plaintext: str):
    """
    Check if the given string is a valid PNG payload.
    
    :param plaintext: The string to check
    :return: True if it's a valid PNG payload, False otherwise
    """
    # Split the string by hyphens
    data = plaintext.split('-')
    print(plaintext[:100])
    # PNG data is stored as "PNG-param,param-data,data,data,...
    # splitting by hyphen should always give 2 separate strings
    print(len(data))
    # Check if there are exactly 3 parts (PNG identifier, dimensions, pixel data)
    if len(data) != 3:
        return False
    # Check if the first part is "PNG"
    if data[0] != "PNG":
        return False
    params = data[1].split(',')
    print(data[1])
     # Check if there are exactly 2 dimension parameters (width and height)
    if len(params) != 2:
        return False
    return True

class PNGPayload:
    width: int
    height: int
    bytes_data: bytes

    def __init__(self, width: int, height: int, bytes_data: bytes):
        self.width = width
        self.height = height
        self.bytes_data = bytes_data

    def convertToPayload(self):
        """
        Convert the PNG data to a string payload.
        
        :return: A string representing the PNG data
        """
        output = []
        output.extend("PNG-")
        output.extend(f"{self.width},{self.height}-")
        lastByte = ""
        for byte in self.bytes_data:
            lastByte = f"{byte},"
            output.extend(lastByte)
        # Remove the final comma

        output[-1] = ""
        output = "".join(output)
        return output

    @staticmethod
    def readFromPath(file_path: str):
        """
        Read a PNG file and create a PNGPayload object.
        
        :param file_path: Path to the PNG file
        :return: PNGPayload object
        """
        with Image.open(file_path) as img:
            img = img.convert('RGBA')
            width, height = img.size

            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            bytes_data = img_byte_arr.getvalue()
            return PNGPayload(width, height, bytes_data)

    @staticmethod
    def readFromString(string: str, output_path: str):
        """
        Reconstruct a PNG image from a payload string and save it.
        
        :param string: The payload string
        :param output_path: Path to save the reconstructed image
        """
        if not isPngPayload(string):
            return
        data = string.split('-')

        # Convert byte data string to bytes
        bytes_data = bytes(map(int, data[2].split(',')))
        
        # Create a new image from bytes
        img = Image.open(io.BytesIO(bytes_data))
        img.save(output_path)

# Sample code for encoding and decoding
if __name__ == "__main__":
    image_to_encode_path = "input/png_medium3.png"
    decoded_img_path = "output/decoded_excision.png"
    # Load PNG data and convert that data into the string that will become the payload
    image_data = PNGPayload.readFromPath(image_to_encode_path)
    payload_string = image_data.convertToPayload()
    test = "MKV"
    decoded_string = ""
    if test == "PNG":
        image_path = "input/excision.png"
        encoded_path = "output/excision.png"
        # Encode the generated string into the png
        encoded_image = png_encode(image_path, payload_string, lsb_bits=5)
        encoded_image.save(encoded_path)
        # Decode the encoded image
        decoded_string = png_decode(encoded_path, lsb_bits=5)
        # Convert the decoded string into a wave file
        PNGPayload.readFromString(decoded_string, decoded_img_path)
    elif test == "WAV":
        input_path = "input/wav_extralong.wav"
        encoded_path = "output/wav_extralong.wav"
        # Encode the generated string into the wav
        encoded_wav = wav_encode(input_path, payload_string, encoded_path, bit_depth=5)
        # Decode the Encoded WAV File
        decoded_string = wav_decode(encoded_path, bit_depth=5)
        # Convert the decoded string into a wave file
        PNGPayload.readFromString(decoded_string, decoded_img_path)
    elif test == "MKV":
        input_path = "input/mkv_medium.mkv"
        encoded_path = "output/mkv_medium.mkv"
        # Encode The generated string into the MKV
        encoded_mkv = mkv_encode(input_path, encoded_path, payload_string, lsb_bits=5)
        # Decode the encoded MKV file
        decoded_string = mkv_decode(encoded_path, lsb_bits=5)
        # Convert the decoded string into a wave file
        PNGPayload.readFromString(decoded_string, decoded_img_path)