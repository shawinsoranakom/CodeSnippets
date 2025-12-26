def add_file_length(source_path: str, compressed: str) -> str:

    file_length = os.path.getsize(source_path)
    file_length_binary = bin(file_length)[2:]
    length_length = len(file_length_binary)

    return "0" * (length_length - 1) + file_length_binary + compressed
