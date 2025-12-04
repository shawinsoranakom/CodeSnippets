def recursive_imply_list(input_list: list[int]) -> int:
  
    if len(input_list) < 2:
        raise ValueError("Input list must contain at least two elements")
    first_implication = imply_gate(input_list[0], input_list[1])
    if len(input_list) == 2:
        return first_implication
    new_list = [first_implication, *input_list[2:]]
    return recursive_imply_list(new_list)

