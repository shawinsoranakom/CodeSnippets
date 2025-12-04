def generate_key(key_size: int) -> tuple[tuple[int, int, int, int], tuple[int, int]]:
    print("Generating prime p...")
    p = rabin_miller.generate_large_prime(key_size)  
    e_1 = primitive_root(p)  
    d = random.randrange(3, p)  
    e_2 = cryptomath.find_mod_inverse(pow(e_1, d, p), p)

    public_key = (key_size, e_1, e_2, p)
    private_key = (key_size, d)

    return public_key, private_key
