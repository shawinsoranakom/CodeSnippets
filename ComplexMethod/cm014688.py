def test_unary_ops(self):
        with torch._jit_internal._disable_emit_hooks():

            def apply(fn):
                return lambda x: fn(x)

            unary_ops = [
                torch.lgamma,
                torch.sigmoid,
                torch.reciprocal,
                torch.neg,
                torch.relu,
                F.relu6,
                torch.log,
                torch.log10,
                torch.log1p,
                torch.log2,
                torch.exp,
                torch.expm1,
                torch.erf,
                torch.erfc,
                torch.cos,
                torch.sin,
                torch.tan,
                torch.acos,
                torch.asin,
                torch.cosh,
                torch.sinh,
                torch.atan,
                torch.tanh,
                F.hardtanh,
                F.hardsigmoid,
                F.hardswish,
                F.softplus,
                F.silu,
                F.mish,
                F.elu,
                torch.sqrt,
                torch.rsqrt,
                torch.abs,
                # TODO broken on int8 since
                # https://github.com/pytorch/pytorch/pull/85144
                # RuntimeError: Invalid integral op_type: 23
                # torch.ceil,
                # torch.floor,
                # torch.round,
                # torch.trunc,
                torch.frac,
                # TODO: broken on ROCm?
                # F.hardshrink,
                F.leaky_relu,
                lambda x: torch.threshold(x, 0, -10),
                # TODO: broken since type promotion was added
                # lambda x: torch.clamp(x, -10, 10),
            ]
            gpu_only = {torch.erf, torch.erfc}
            sizes = [(1,), (2,), (4, 4)]
            for dtype, op, device, size in product(
                self.dtypes, unary_ops, self.devices, sizes
            ):
                # TODO: Add back when https://github.com/pytorch/pytorch/issues/55905 is closed
                if dtype in [torch.float16, torch.bfloat16] and device == "cpu":
                    continue
                # todo - re-enable. fails with .500
                if dtype == torch.bfloat16 and op == torch.round:
                    continue
                if op in gpu_only and device == "cpu":
                    continue
                try:
                    x = self.data_for(dtype, device, size=size)
                    fn = apply(op)
                    ref = fn(x)
                except Exception:
                    # If eager mode doesn't support a dtype/op/device combo,
                    # neither does the fuser.  Catch everything to avoid needing to
                    # guess what errors might be thrown by eager.
                    continue
                try:
                    t = torch.jit.trace(fn, (x,))
                    torch.testing.assert_close(ref, t(x))
                    self.assertAllFused(t.graph_for(x))
                except Exception as e:
                    raise RuntimeError(
                        " ".join(
                            ["Failed:", str(dtype), op.__name__, device, str(size)]
                        )
                    ) from e