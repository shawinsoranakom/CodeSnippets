def test_scrypt_decode(self):
        encoded = make_password("lètmein", "seasalt", "scrypt")
        hasher = get_hasher("scrypt")
        decoded = hasher.decode(encoded)
        tests = [
            ("block_size", hasher.block_size),
            ("parallelism", hasher.parallelism),
            ("salt", "seasalt"),
            ("work_factor", hasher.work_factor),
        ]
        for key, excepted in tests:
            with self.subTest(key=key):
                self.assertEqual(decoded[key], excepted)