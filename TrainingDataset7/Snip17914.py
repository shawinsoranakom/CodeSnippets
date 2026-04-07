def test_scrypt_upgrade(self):
        tests = [
            ("work_factor", "work factor", 2**11),
            ("block_size", "block size", 10),
            ("parallelism", "parallelism", 2),
        ]
        for attr, summary_key, new_value in tests:
            with self.subTest(attr=attr):
                self._test_scrypt_upgrade(attr, summary_key, new_value)