def generate_key(key_size: int) -> tuple[tuple[int, int], tuple[int, int]]:
    p = rabin_miller.generate_large_prime(key_size)
    q = rabin_miller.generate_large_prime(key_size)
    n = p * q

    while True:
        e = random.randrange(2 ** (key_size - 1), 2 ** (key_size))
        if gcd_by_iterative(e, (p - 1) * (q - 1)) == 1:
            break

    d = cryptomath_module.find_mod_inverse(e, (p - 1) * (q - 1))

    public_key = (n, e)
    private_key = (n, d)
    return (public_key, private_key)
