def gray_code(bit_count: int) -> list:

    if bit_count < 0:
        raise ValueError("The given input must be positive")

    sequence = gray_code_sequence_string(bit_count)
    
    for i in range(len(sequence)):
        sequence[i] = int(sequence[i], 2)

    return sequence

