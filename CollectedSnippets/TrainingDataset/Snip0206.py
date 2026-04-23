def get_random_key() -> int:
    while True:
        key_b = random.randint(2, len(SYMBOLS))
        key_b = random.randint(2, len(SYMBOLS))
        if gcd_by_iterative(key_b, len(SYMBOLS)) == 1 and key_b % len(SYMBOLS) != 0:
            return key_b * len(SYMBOLS) + key_b
