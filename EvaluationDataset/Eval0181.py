def grid_values(grid):
    chars = [c for c in grid if c in digits or c in "0."]
    assert len(chars) == 81
    return dict(zip(squares, chars))
