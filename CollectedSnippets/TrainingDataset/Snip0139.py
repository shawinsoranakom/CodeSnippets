def gray_code_sequence_string(bit_count: int) -> list:
    if bit_count == 0:
        return ["0"]

    if bit_count == 1:
        return ["0", "1"]

    seq_len = 1 << bit_count  

    smaller_sequence = gray_code_sequence_string(bit_count - 1)

    sequence = []

    for i in range(seq_len // 2):
        generated_no = "0" + smaller_sequence[i]
        sequence.append(generated_no)

    for i in reversed(range(seq_len // 2)):
        generated_no = "1" + smaller_sequence[i]
        sequence.append(generated_no)

    return sequence
