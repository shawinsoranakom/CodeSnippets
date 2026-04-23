def _pointwise_test(
        self,
        op,
        ref,
        inputs,
        is_fastpath,
        is_inplace,
        *,
        scalars=None,
        custom_values_err=None,
        **kwargs,
    ):
        ref_inputs = (
            [[t.detach().clone() for t in inputs[0]], inputs[1], inputs[2]]
            if is_inplace
            else inputs
        )
        try:
            with (
                InplaceForeachVersionBumpCheck(self, inputs[0])
                if is_inplace
                else nullcontext()
            ):
                actual = op(inputs, self.is_cuda, is_fastpath, **kwargs)
        except RuntimeError as e:
            with self.assertRaisesRegex(type(e), re.escape(str(e).splitlines()[0])):
                ref(ref_inputs, **kwargs)
        else:
            expected = ref(ref_inputs, **kwargs)
            self.assertEqual(expected, actual)
        if scalars is not None:
            kwargs = kwargs.copy()
            kwargs["scalars"] = scalars
            try:
                actual = op(inputs, self.is_cuda, is_fastpath, **kwargs)
            except RuntimeError as e:
                # Match with error messages from regular non-foreach reference if no
                # custom error message was provided.
                if custom_values_err is None:
                    with self.assertRaisesRegex(
                        type(e), re.escape(str(e).splitlines()[0])
                    ):
                        ref(ref_inputs, **kwargs)
                else:
                    self.assertEqual(re.escape(str(e)), re.escape(custom_values_err))
            else:
                expected = ref(ref_inputs, **kwargs)
                self.assertEqual(expected, actual)