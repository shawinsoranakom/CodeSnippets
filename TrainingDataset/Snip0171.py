def truth_table(func: Callable) -> str:

    def make_table_row(items: list | tuple) -> str:
 
        return f"| {' | '.join(f'{item:^8}' for item in items)} |"

    return "\n".join(
        (
            "Truth Table of NOR Gate:",
            make_table_row(("Input 1", "Input 2", "Output")),
            *[make_table_row((i, j, func(i, j))) for i in (0, 1) for j in (0, 1)],
        )
    )
