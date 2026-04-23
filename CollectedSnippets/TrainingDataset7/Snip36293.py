def test_force_str_DjangoUnicodeDecodeError(self):
        reason = "unexpected end of data" if PYPY else "invalid start byte"
        msg = (
            f"'utf-8' codec can't decode byte 0xff in position 0: {reason}. "
            "You passed in b'\\xff' (<class 'bytes'>)"
        )
        with self.assertRaisesMessage(DjangoUnicodeDecodeError, msg):
            force_str(b"\xff")