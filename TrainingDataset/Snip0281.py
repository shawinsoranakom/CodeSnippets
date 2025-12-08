def generate_large_prime(keysize: int = 1024) -> int:
    while True:
        num = random.randrange(2 ** (keysize - 1), 2 ** (keysize))
        if is_prime_low_num(num):
            return num
