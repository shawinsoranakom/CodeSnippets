def generate_all_subsequences(sequence: list[Any]) -> None:
    create_state_space_tree(sequence, [], 0)
