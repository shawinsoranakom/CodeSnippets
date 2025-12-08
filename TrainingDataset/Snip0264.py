def generate_permutation_key(block_size: int) -> list[int]:
    digits = list(range(block_size))
    random.shuffle(digits)
    return digits
