def test_variant_consistency_jit(self, device, dtype, op):
        _requires_grad = dtype in op.supported_backward_dtypes(
            torch.device(device).type
        )

        include_conjugated_inputs = op.test_conjugated_samples and dtype.is_complex
        samples = op.sample_inputs(
            device,
            dtype,
            requires_grad=_requires_grad,
            include_conjugated_inputs=include_conjugated_inputs,
        )

        # Acquires variants to test
        func = op.get_op()
        method = op.get_method()
        variants = {
            # TODO: inplace tests currently fail, fix and add inplace variant
            "function": func,
            "method": method,
        }

        # scripting strips the torch.ops prefix from these operators
        # incorrectly; don't bother testing this case.  Count this
        # as "testing"
        if isinstance(func, torch._ops.OpOverload):
            self.skipTest("variant consistency doesn't work on torch.ops")

        # TODO: find better way to standardize on op registration itself..
        has_fake_function = op.name in ["resize_", "resize_as_"]

        if has_fake_function:
            variants = {"method": getattr(torch.Tensor, op.name)}
            samples = op.sample_inputs(device, dtype, requires_grad=False)

        tested = False
        for sample in samples:
            # Test traced and scripted consistency
            for func_type, variant in variants.items():
                if variant is None:
                    continue

                # scripting and check_alias_analysis do not work with lambdas
                # lambdas are typically used as a way to simulate methods without
                # functional variants, so rely on the other variant for testing
                # for now
                if is_lambda(variant):
                    continue

                tested = True
                try:
                    self.indiv_variant_test_jit(
                        device, dtype, op, sample, func_type, variant, has_fake_function
                    )
                except Exception as e:
                    variant_error_info = dedent(
                        f"""
                        Error testing {op.name} {func_type} variant
                        with dtype: {dtype}
                        with inputs {sample}:
                    """
                    )
                    raise Exception(variant_error_info) from e  # noqa: TRY002

        if not tested:
            raise AssertionError("JIT Test does not execute any logic")