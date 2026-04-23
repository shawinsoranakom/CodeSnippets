def test_binary_ops(self):
        def apply(fn):
            return lambda x, y: fn(x, y)

        binary_ops = [
            operator.__and__,
            operator.__or__,
            operator.__xor__,
            torch.add,
            torch.sub,
            torch.mul,
            torch.min,
            torch.max,
            lambda x, y: torch.lerp(x, y, 0.5),
            torch.atan2,
            torch.div,
            torch.eq,
            torch.ne,
            torch.ge,
            torch.gt,
            torch.lt,
            torch.fmod,
            torch.remainder,
            lambda x, y: y.type_as(x),
        ]
        fp_only = [
            torch.fmod,
            torch.remainder,
        ]
        devices = self.devices
        for dtype, op, device in product(self.dtypes, binary_ops, devices):
            if dtype in [torch.float16, torch.bfloat16] and device == "cpu":
                continue
            try:
                x = self.data_for(dtype, device)
                y = self.data_for(dtype, device)
                fn = apply(op)
                ref = fn(x, y)
            except Exception:
                # If eager mode doesn't support a dtype/op/device combo,
                # neither does the fuser.  Catch everything to avoid needing to
                # guess what errors might be thrown by eager.
                continue
            try:
                t = torch.jit.trace(fn, (x, y))
                self.assertEqual(ref, t(x, y))
                if op not in fp_only or dtype.is_floating_point:
                    self.assertAllFused(t.graph_for(x, y))
            except Exception as e:
                raise RuntimeError(
                    " ".join(["Failed:", str(dtype), op.__name__, device])
                ) from e