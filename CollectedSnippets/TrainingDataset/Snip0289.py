def encrypt_message(
    message: str, key: tuple[int, int], block_size: int = DEFAULT_BLOCK_SIZE
) -> list[int]:
    encrypted_blocks = []
    n, e = key

    for block in get_blocks_from_text(message, block_size):
        encrypted_blocks.append(pow(block, e, n))
    return encrypted_blocks
