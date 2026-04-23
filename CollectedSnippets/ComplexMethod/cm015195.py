def test_outputs_can_any_pytree(self, device):
        x = torch.randn(2, 3, device=device)
        t = torch.randn(2, 3, device=device)

        for output in [None, ()]:
            with self.assertRaisesRegex(
                RuntimeError,
                r"jvp\(f, primals, tangents\): Expected f to be a function that has non-empty output",
            ):
                jvp(lambda _: output, (x,), (t,))

        for output in [1, True, 12.2, "abc"]:
            with self.assertRaisesRegex(
                RuntimeError,
                r"jvp\(f, primals, tangents\): expected f\(\*primals\) to return only tensors",
            ):
                jvp(lambda _: output, (x,), (t,))

        # Check list output
        out = jvp(lambda x: [x, x.sum()], (x,), (t,))
        for i in range(2):
            if not (isinstance(out[i], list) and len(out[i]) == 2):
                raise AssertionError(
                    f"Expected list of length 2, got {type(out[i]).__name__} of length {len(out[i])}"
                )

        # Check dict output
        out = jvp(lambda x: {"x": x, "xsum": x.sum()}, (x,), (t,))
        for i in range(2):
            if not (isinstance(out[i], dict) and len(out[i]) == 2 and "xsum" in out[i]):
                raise AssertionError(
                    f"Expected dict of length 2 with 'xsum' key, got {type(out[i]).__name__}"
                )

        def composite_output(x):
            out = x.sum()
            return [
                (out, {"a": x, "out": [x, out]}),
            ]

        out = jvp(composite_output, (x,), (t,))
        for i in range(2):
            if not isinstance(out[i], list):
                raise AssertionError(f"Expected list, got {type(out[i]).__name__}")
            if not (isinstance(out[i][0], tuple) and isinstance(out[i][0][1], dict)):
                raise AssertionError(
                    f"Expected (tuple, dict) structure, got ({type(out[i][0]).__name__}, {type(out[i][0][1]).__name__})"
                )