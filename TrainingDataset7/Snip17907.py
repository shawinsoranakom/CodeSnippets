def test_argon2_decode(self):
        salt = "abcdefghijk"
        encoded = make_password("lètmein", salt=salt, hasher="argon2")
        hasher = get_hasher("argon2")
        decoded = hasher.decode(encoded)
        self.assertEqual(decoded["memory_cost"], hasher.memory_cost)
        self.assertEqual(decoded["parallelism"], hasher.parallelism)
        self.assertEqual(decoded["salt"], salt)
        self.assertEqual(decoded["time_cost"], hasher.time_cost)