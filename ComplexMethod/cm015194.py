def test_outputs_can_any_pytree(self, device, jacapi):
        x = torch.randn(2, 3, device=device)

        for output in [None, ()]:
            with self.assertRaisesRegex(
                RuntimeError,
                r"(vjp|jvp).+: Expected f to be a function that has non-empty output",
            ):
                jacapi(lambda _: output)(x)

        for output in [1, True, 12.2, "abc"]:
            with self.assertRaisesRegex(
                RuntimeError,
                r"(vjp|jvp).+: expected f\(\*primals\) to return only tensors",
            ):
                jacapi(lambda _: output)(x)

        # Check list output
        out = jacapi(lambda x: [x, x.sum()])(x)
        if not (isinstance(out, list) and len(out) == 2):
            raise AssertionError(
                f"Expected list of length 2, got {type(out).__name__} of length {len(out)}"
            )

        # Check dict output
        out = jacapi(lambda x: {"x": x, "xsum": x.sum()})(x)
        if not (isinstance(out, dict) and len(out) == 2 and "xsum" in out):
            raise AssertionError(
                f"Expected dict of length 2 with 'xsum' key, got {type(out).__name__}"
            )

        def composite_output(x):
            out = x.sum()
            return [
                (out, {"a": x, "out": [x, out]}),
            ]

        out = jacapi(composite_output)(x)
        if not isinstance(out, list):
            raise AssertionError(f"Expected list, got {type(out).__name__}")
        if not (isinstance(out[0], tuple) and isinstance(out[0][1], dict)):
            raise AssertionError(
                f"Expected (tuple, dict) structure, got ({type(out[0]).__name__}, {type(out[0][1]).__name__})"
            )