def test_to_python_int_values(self):
        self.assertEqual(
            models.UUIDField().to_python(0),
            uuid.UUID("00000000-0000-0000-0000-000000000000"),
        )
        # Works for integers less than 128 bits.
        self.assertEqual(
            models.UUIDField().to_python((2**128) - 1),
            uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        )