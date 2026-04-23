def test_binary(self, a, op, b):
        try:
            r = eval(f"a {op} b")
        except Exception as e:
            r = e

        any_tensor = isinstance(a, torch.Tensor) or isinstance(b, torch.Tensor)
        any_float = _any_float(a, b)
        returns_float = any_float or op in BINARY_RETURNS_FLOAT

        if op == MM:
            if not (isinstance(a, torch.Tensor) and isinstance(b, torch.Tensor)):
                self.assertIsInstance(r, TypeError)
            elif a is b:
                self.assertIsInstance(r, torch.Tensor)
            else:
                self.assertIsInstance(r, RuntimeError)

        elif any_tensor:
            if op in BINARY_ACCEPTS_INT_ONLY and any_float:
                # See https://github.com/pytorch/pytorch/issues/15754
                self.assertIsInstance(r, NotImplementedError)
            else:
                self.assertIsInstance(r, torch.Tensor)

                if op in BINARY_RETURNS_BOOL:
                    self.assertEqual(r.dtype, torch.bool)
                elif op in BINARY_ACCEPTS_INT_ONLY:
                    self.assertFalse(r.dtype.is_floating_point)
                elif op in BINARY_ACCEPTS_FLOAT_OR_INT:
                    self.assertEqual(r.dtype.is_floating_point, returns_float)
                else:
                    self.assertFalse("Logic error")

        elif op in BINARY_RETURNS_BOOL:
            self.assertIsInstance(r, bool)

        elif op in BINARY_ACCEPTS_INT_ONLY:
            if any_float:
                self.assertIsInstance(r, TypeError)
            else:
                self.assertIsInstance(r, int)

        elif returns_float:
            self.assertIsInstance(r, float)

        else:
            self.assertIsInstance(r, int)