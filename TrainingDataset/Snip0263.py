def generate_valid_block_size(message_length: int) -> int:
    block_sizes = [
        block_size
        for block_size in range(2, message_length + 1)
        if message_length % block_size == 0
    ]
    return random.choice(block_sizes)
