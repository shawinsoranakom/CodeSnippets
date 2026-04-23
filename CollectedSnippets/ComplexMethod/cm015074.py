def _binary_test(
        self,
        dtype,
        op,
        ref,
        inputs,
        is_fastpath,
        is_inplace,
        *,
        alpha,
        scalar_self_arg: bool,
    ):
        ref_inputs = (
            [[t.detach().clone() for t in inputs[0]], inputs[1]]
            if is_inplace
            else inputs
        )
        try:
            with (
                InplaceForeachVersionBumpCheck(self, inputs[0])
                if op.is_inplace
                else nullcontext()
            ):
                actual = op(inputs, self.is_cuda, is_fastpath)
        except RuntimeError as e:
            with self.assertRaisesRegex(type(e), re.escape(str(e).splitlines()[0])):
                if not scalar_self_arg:
                    ref(ref_inputs)
                else:
                    [ref.func(ref_inputs[0], t) for t in ref_inputs[1]]
        else:
            expected = (
                ref(ref_inputs)
                if not scalar_self_arg
                else [ref.func(ref_inputs[0], t) for t in ref_inputs[1]]
            )
            self.assertEqual(actual, expected)
        if alpha is not None and not scalar_self_arg:
            kwargs = {"alpha": alpha}
            ref_inputs = inputs
            try:
                op_kwargs = {}
                op_kwargs.update(kwargs)
                with (
                    InplaceForeachVersionBumpCheck(self, inputs[0])
                    if op.is_inplace
                    else nullcontext()
                ):
                    actual = op(inputs, self.is_cuda, is_fastpath, **op_kwargs)
            except RuntimeError as e:
                with self.assertRaisesRegex(type(e), re.escape(str(e).splitlines()[0])):
                    ref(ref_inputs, **kwargs)
            else:
                expected = ref(ref_inputs, **kwargs)
                if dtype in (torch.float16, torch.bfloat16) and TEST_WITH_ROCM:
                    self.assertEqual(
                        expected, actual, atol=1.0e-3, rtol=default_tolerances(dtype)[0]
                    )
                else:
                    self.assertEqual(expected, actual)