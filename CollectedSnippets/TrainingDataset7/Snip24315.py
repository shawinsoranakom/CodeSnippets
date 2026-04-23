def assertArgumentTypeError(self, i, bad_type):
        if PY312:
            msg = (
                f"argument {i}: TypeError: '{bad_type}' object cannot be interpreted "
                "as an integer"
            )
        else:
            msg = f"argument {i}: TypeError: wrong type"
        return self.assertRaisesMessage(ctypes.ArgumentError, msg)