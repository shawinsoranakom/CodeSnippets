def test_short_halfway_cases(self):
        # exact halfway cases with a small number of significant digits
        for k in 0, 5, 10, 15, 20:
            # upper = smallest integer >= 2**54/5**k
            upper = -(-2**54//5**k)
            # lower = smallest odd number >= 2**53/5**k
            lower = -(-2**53//5**k)
            if lower % 2 == 0:
                lower += 1
            for i in range(TEST_SIZE):
                # Select a random odd n in [2**53/5**k,
                # 2**54/5**k). Then n * 10**k gives a halfway case
                # with small number of significant digits.
                n, e = random.randrange(lower, upper, 2), k

                # Remove any additional powers of 5.
                while n % 5 == 0:
                    n, e = n // 5, e + 1
                assert n % 10 in (1, 3, 7, 9)

                # Try numbers of the form n * 2**p2 * 10**e, p2 >= 0,
                # until n * 2**p2 has more than 20 significant digits.
                digits, exponent = n, e
                while digits < 10**20:
                    s = '{}e{}'.format(digits, exponent)
                    self.check_strtod(s)
                    # Same again, but with extra trailing zeros.
                    s = '{}e{}'.format(digits * 10**40, exponent - 40)
                    self.check_strtod(s)
                    digits *= 2

                # Try numbers of the form n * 5**p2 * 10**(e - p5), p5
                # >= 0, with n * 5**p5 < 10**20.
                digits, exponent = n, e
                while digits < 10**20:
                    s = '{}e{}'.format(digits, exponent)
                    self.check_strtod(s)
                    # Same again, but with extra trailing zeros.
                    s = '{}e{}'.format(digits * 10**40, exponent - 40)
                    self.check_strtod(s)
                    digits *= 5
                    exponent -= 1