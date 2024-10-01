import os

msg_delim = "\x00"
msg_delim_len = len(msg_delim)

msg_delim_binary = ''.join(format(ord(c), '08b') for c in msg_delim)
msg_delim_binary_len = len(msg_delim_binary)

def get_text_from_file(text_file_path: str):
    """
    Extracts string from provided text file.
    :param text_file_path: Path to the text file.
    :return:
    """
    try:
        with(open(text_file_path, 'r', encoding='utf-8')) as file:
            return file.read().encode('ascii', 'ignore').decode('ascii')
    except FileNotFoundError:
        return ""

def delete_file(input_path: str):
    """
    Attempts to delete the file at the specified path.
    :param input_path: The path to the file to delete.
    """
    # Delete the audio file
    try:
        os.remove(input_path)
        print(f"Temporary file {input_path} deleted successfully.")
    except OSError as e:
        print(f"Unable to delete {input_path}. Error: {e}")
        pass

def process_payload(msg: str):
    """
    preprocesses the message before encoding into the message.
    :param msg: The message to be encoded.
    :return: The message with the delimiter appended to the end.
    """
    output = msg + msg_delim
    return output

def msg_to_bin(msg: str):
    """
    Converts a string message into its binary representation.
    :param msg: The message to be sent.
    :return: Returns the message as a binary string.
    """
    return ''.join(format(ord(c), '08b') for c in msg)

def bin_to_msg(bin_data: list):
    """
    Converts the list of binary data into an ascii string.
    :param bin_data: A list of each bit in the binary data.
    :return: An ascii string of the message.
    """
    message = []
    bin_data_len = len(bin_data)
    # Iterate through the binary data list, 8 characters at a time
    for i in range(0, bin_data_len, 8):
        # Convert the current byte to an ascii character
        byte = ''.join(bin_data[i:i + 8])
        char = chr(int(byte, 2))
        # If that character
        if char == msg_delim_binary:
            break
        message.append(char)
    # Convert output list to a string and return it
    return ''.join(message).rstrip(msg_delim)

def delim_check(bin_msg: list):
    # Get the final few characters of the binary message (as much as required)
    bin_msg_end = ''.join(bin_msg[-msg_delim_binary_len:])
    return bin_msg_end == msg_delim_binary


