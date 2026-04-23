def test_vjp_outputs_can_any_pytree(self, device):
        x = torch.randn(2, 3, device=device)
        t = torch.randn(2, 3, device=device)

        for output in [None, ()]:
            with self.assertRaisesRegex(
                RuntimeError,
                r"vjp\(f, \*primals\): Expected f to be a function that has non-empty output",
            ):
                _, vjp_fn = vjp(lambda _: output, x)
                vjp_fn(t)

        for output in [1, True, 12.2, "abc"]:
            with self.assertRaisesRegex(
                RuntimeError,
                r"vjp\(f, \*primals\): expected f\(\*primals\) to return only tensors",
            ):
                _, vjp_fn = vjp(lambda _: output, x)
                vjp_fn(t)

        # Check list output
        output, vjp_fn = vjp(lambda x: [x, x.sum()], x)
        (vjp_out,) = vjp_fn([t, t.sum()])
        if not isinstance(output, list) or len(output) != 2:
            raise AssertionError(f"Expected list of length 2, got {type(output)}")
        if not isinstance(vjp_out, torch.Tensor):
            raise AssertionError(f"Expected Tensor, got {type(vjp_out)}")

        # Check dict output
        output, vjp_fn = vjp(lambda x: {"x": x, "xsum": x.sum()}, x)
        (vjp_out,) = vjp_fn({"x": t, "xsum": t.sum()})
        if not isinstance(output, dict) or len(output) != 2 or "xsum" not in output:
            raise AssertionError(f"Expected dict with 'xsum', got {output}")
        if not isinstance(vjp_out, torch.Tensor):
            raise AssertionError(f"Expected Tensor, got {type(vjp_out)}")

        def composite_output(x):
            out = x.sum()
            return [
                (out, {"a": x, "out": [x, out]}),
            ]

        output, vjp_fn = vjp(composite_output, x)
        (vjp_out,) = vjp_fn(
            [
                (t.sum(), {"a": t, "out": [t, t.sum()]}),
            ]
        )
        if not isinstance(output, list):
            raise AssertionError(f"Expected list, got {type(output)}")
        if not isinstance(output[0], tuple) or not isinstance(output[0][1], dict):
            raise AssertionError(f"Expected tuple with dict, got {output[0]}")
        if not isinstance(vjp_out, torch.Tensor):
            raise AssertionError(f"Expected Tensor, got {type(vjp_out)}")