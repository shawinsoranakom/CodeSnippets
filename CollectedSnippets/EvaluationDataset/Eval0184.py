def display(values):
    width = 1 + max(len(values[s]) for s in squares)
    line = "+".join(["-" * (width * 3)] * 3)
    for r in rows:
        print(
            "".join(
                values[r + c].center(width) + ("|" if c in "36" else "") for c in cols
            )
        )
        if r in "CF":
            print(line)
    print()
