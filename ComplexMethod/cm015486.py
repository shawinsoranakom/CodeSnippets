def _test_non_float_param(
        self,
        non_float_dtypes: list,
        mp_policy: MixedPrecisionPolicy,
        frozen_float: bool,
    ):
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(16, 16)
                if frozen_float:
                    self.frozen_float = nn.Parameter(
                        torch.randn(16), requires_grad=False
                    )
                for i, dtype in enumerate(non_float_dtypes):
                    self.register_parameter(
                        f"non_float_{i}",
                        nn.Parameter(
                            torch.randint(0, 127, (16,), dtype=dtype),
                            requires_grad=False,
                        ),
                    )

            def forward(self, x):
                return self.linear(x)

        model = Model()
        fully_shard(model, mp_policy=mp_policy)
        for p in model.parameters():
            self.assertEqual(p.size(0) % self.world_size, 0)
        ag_input_dtypes = set()
        expected_ag_output_bytes = 0
        for p in model.parameters():
            if p.dtype.is_floating_point and mp_policy.param_dtype is not None:
                ag_input_dtypes.add(mp_policy.param_dtype)
                expected_ag_output_bytes += p.numel() * mp_policy.param_dtype.itemsize
            else:
                # Non-float params keep their original dtype; param_dtype
                # only applies to floating-point params
                ag_input_dtypes.add(p.dtype)
                expected_ag_output_bytes += p.numel() * p.element_size()
        expected_ag_dtype = (
            next(iter(ag_input_dtypes)) if len(ag_input_dtypes) == 1 else torch.uint8
        )
        orig_ag = dist.all_gather_into_tensor

        def assert_all_gather(*args, **kw):
            output = kw.get("output", args[0] if len(args) > 0 else None)
            input = kw.get("input_tensor", args[1] if len(args) > 1 else None)
            self.assertEqual(input.dtype, expected_ag_dtype)
            self.assertEqual(output.nbytes, expected_ag_output_bytes)
            return orig_ag(*args, **kw)

        expected_rs_input_numel = sum(
            p.numel() for p in model.parameters() if p.requires_grad
        )
        orig_rs = dist.reduce_scatter_tensor

        def assert_reduce_scatter(*args, **kw):
            input = kw.get("input", args[1] if len(args) > 1 else None)
            self.assertEqual(input.numel(), expected_rs_input_numel)
            return orig_rs(*args, **kw)

        x = torch.randn(4, 16, device=device_type)
        with (
            patch_all_gather(assert_all_gather),
            patch_reduce_scatter(assert_reduce_scatter),
        ):
            loss = model(x).sum()
            loss.backward()