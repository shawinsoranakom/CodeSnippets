def test_not_primes(self):
        with pytest.raises(ValueError):
            is_prime(-19)
        assert not is_prime(0), (
            "Zero doesn't have any positive factors, primes must have exactly two."
        )
        assert not is_prime(1), (
            "One only has 1 positive factor, primes must have exactly two."
        )
        assert not is_prime(2 * 2)
        assert not is_prime(2 * 3)
        assert not is_prime(3 * 3)
        assert not is_prime(3 * 5)
        assert not is_prime(3 * 5 * 7)