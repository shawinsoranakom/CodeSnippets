def test_sample_input(self) -> None:
        a, b, c, d, e = (object() for _ in range(5))

        # Construction with natural syntax
        s = SampleInput(a, b, c, d=d, e=e)
        if s.input is not a:
            raise AssertionError("s.input should be a")
        if s.args != (b, c):
            raise AssertionError(f"s.args should be (b, c), got {s.args}")
        if s.kwargs != dict(d=d, e=e):
            raise AssertionError(f"s.kwargs mismatch: got {s.kwargs}")

        # Construction with explicit args and kwargs
        s = SampleInput(a, args=(b,), kwargs=dict(c=c, d=d, e=e))
        if s.input is not a:
            raise AssertionError("s.input should be a")
        if s.args != (b,):
            raise AssertionError(f"s.args should be (b,), got {s.args}")
        if s.kwargs != dict(c=c, d=d, e=e):
            raise AssertionError(f"s.kwargs mismatch: got {s.kwargs}")

        # Construction with a mixed form will error
        with self.assertRaises(AssertionError):
            s = SampleInput(a, b, c, args=(d, e))

        with self.assertRaises(AssertionError):
            s = SampleInput(a, b, c, kwargs=dict(d=d, e=e))

        with self.assertRaises(AssertionError):
            s = SampleInput(a, args=(b, c), d=d, e=e)

        with self.assertRaises(AssertionError):
            s = SampleInput(a, b, c=c, kwargs=dict(d=d, e=e))

        # Mixing metadata into "natural" construction will error
        with self.assertRaises(AssertionError):
            s = SampleInput(a, b, name="foo")

        with self.assertRaises(AssertionError):
            s = SampleInput(a, b, output_process_fn_grad=lambda x: x)

        with self.assertRaises(AssertionError):
            s = SampleInput(a, b, broadcasts_input=True)

        # But when only input is given, metadata is allowed for backward
        # compatibility
        s = SampleInput(a, broadcasts_input=True)
        if s.input is not a:
            raise AssertionError("s.input should be a")
        if not s.broadcasts_input:
            raise AssertionError("s.broadcasts_input should be True")