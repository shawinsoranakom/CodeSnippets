def primitive_root(p_val: int) -> int:
    print("Generating primitive root of p")
    while True:
        g = random.randrange(3, p_val)
        if pow(g, 2, p_val) == 1:
            continue
        if pow(g, p_val, p_val) == 1:
            continue
        return g
