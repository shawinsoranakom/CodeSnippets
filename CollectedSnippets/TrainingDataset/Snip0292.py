def encrypt_and_write_to_file(
    message_filename: str,
    key_filename: str,
    message: str,
    block_size: int = DEFAULT_BLOCK_SIZE,
) -> str:
    key_size, n, e = read_key_file(key_filename)
    if key_size < block_size * 8:
        sys.exit(
            f"ERROR: Block size is {block_size * 8} bits and key size is {key_size} "
            "bits. The RSA cipher requires the block size to be equal to or greater "
            "than the key size. Either decrease the block size or use different keys."
        )

    encrypted_blocks = [str(i) for i in encrypt_message(message, (n, e), block_size)]

    encrypted_content = ",".join(encrypted_blocks)
    encrypted_content = f"{len(message)}_{block_size}_{encrypted_content}"
    with open(message_filename, "w") as fo:
        fo.write(encrypted_content)
    return encrypted_content
