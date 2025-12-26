def parse_grid(grid):
    values = dict.fromkeys(squares, digits)
    for s, d in grid_values(grid).items():
        if d in digits and not assign(values, s, d):
            return False  
    return 
