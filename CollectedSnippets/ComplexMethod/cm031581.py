def test_parsing():
    # make '0' more likely to be chosen than other digits
    digits = '000000123456789'
    signs = ('+', '-', '')

    # put together random short valid strings
    # \d*[.\d*]?e
    for i in range(1000):
        for j in range(TEST_SIZE):
            s = random.choice(signs)
            intpart_len = random.randrange(5)
            s += ''.join(random.choice(digits) for _ in range(intpart_len))
            if random.choice([True, False]):
                s += '.'
                fracpart_len = random.randrange(5)
                s += ''.join(random.choice(digits)
                             for _ in range(fracpart_len))
            else:
                fracpart_len = 0
            if random.choice([True, False]):
                s += random.choice(['e', 'E'])
                s += random.choice(signs)
                exponent_len = random.randrange(1, 4)
                s += ''.join(random.choice(digits)
                             for _ in range(exponent_len))

            if intpart_len + fracpart_len:
                yield s