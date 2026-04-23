def test_binary_op_tensors_on_different_devices(self, device, dtype, op):
        _cuda_tensors = next(
            iter(
                op.sample_inputs(
                    device,
                    dtype,
                    num_input_tensors=[2],
                    same_size=True,
                    allow_higher_dtype_scalars=True,
                )
            )
        ).input
        _cpu_tensors = next(
            iter(
                op.sample_inputs(
                    "cpu",
                    dtype,
                    num_input_tensors=[2],
                    same_size=True,
                    allow_higher_dtype_scalars=True,
                )
            )
        ).input
        tensors1, tensors2 = list(zip(_cuda_tensors, _cpu_tensors))

        foreach_op, foreach_op_ = op.method_variant, op.inplace_variant
        native_op, native_op_ = op.ref, op.ref_inplace
        try:
            actual = foreach_op(tensors1, tensors2)
        except RuntimeError as e:
            with self.assertRaisesRegex(type(e), re.escape(str(e).splitlines()[0])):
                [native_op(t1, t2) for t1, t2 in zip(tensors1, tensors2)]
        else:
            expected = [native_op(t1, t2) for t1, t2 in zip(tensors1, tensors2)]
            self.assertEqual(expected, actual)
        try:
            foreach_op_(tensors1, tensors2)
        except RuntimeError as e:
            with self.assertRaisesRegex(type(e), re.escape(str(e).splitlines()[0])):
                [native_op_(t1, t2) for t1, t2 in zip(tensors1, tensors2)]
        else:
            self.assertEqual(actual, tensors1)