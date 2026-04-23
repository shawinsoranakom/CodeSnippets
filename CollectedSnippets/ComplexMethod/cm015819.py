def _test_code_common(
        self,
        mod,
        inputs,
        include_ops,
        exclude_ops,
        atol=1e-5,
        rtol=1.3e-6,
        check_quantization=False,
        check_dynamic=None,
        num_include_ops=None,
        quantizer=None,
    ):
        with torch.no_grad():
            clone_inputs = self._clone_inputs(inputs)
            if check_quantization:
                raise NotImplementedError("not supported, please migrate to torchao")
                """
                mod = _generate_qdq_quantized_model(mod, inputs, quantizer=quantizer)
                """
            expected = mod(*inputs)
            actual, (source_code,) = run_and_get_code(
                torch.compile(mod, fullgraph=True, dynamic=check_dynamic),
                *clone_inputs,
            )
            assert_keywords = ["assert_size_stride", "assert_alignment"]
            filtered_lines = [
                line
                for line in source_code.splitlines()
                if not any(assert_key in line for assert_key in assert_keywords)
            ]
            source_code = "\n".join(filtered_lines)

            for op in include_ops:
                self.assertIn(op, source_code)
            if num_include_ops is not None:
                if len(include_ops) != len(num_include_ops):
                    raise AssertionError(
                        f"len(include_ops)={len(include_ops)} != len(num_include_ops)={len(num_include_ops)}"
                    )
                for i in range(len(include_ops)):
                    self.assertEqual(
                        source_code.count(include_ops[i]), num_include_ops[i]
                    )
            for op in exclude_ops:
                self.assertNotIn(op, source_code)
            if check_dynamic is not None:
                _check_has_dynamic_shape(self, source_code)
            if not check_quantization:
                # Skip due to reduce range setting for Quantization on preCI system.
                torch.testing.assert_close(actual, expected, atol=atol, rtol=rtol)