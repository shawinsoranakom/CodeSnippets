def test_bytes_decode_error(self):
        with self.assertRaisesMessage(ValueError, "Unsupported value"):
            normalize_json(b"\xff")