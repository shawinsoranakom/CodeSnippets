def test_parity(self, device, dtype, op, noncontiguous, inplace):
        if inplace:
            _, _, func, ref = self._get_funcs(op)
        else:
            func, ref, _, _ = self._get_funcs(op)
        for sample in op.sample_inputs(
            device, dtype, noncontiguous=noncontiguous, allow_higher_dtype_scalars=True
        ):
            ref_kwargs = sample.kwargs
            # div promotes ints to floats, so we cannot go on the fastpath there
            div_slowpath = (
                dtype in integral_types_and(torch.bool) and op.name == "_foreach_div"
            )
            expect_fastpath = not (
                noncontiguous or sample.disable_fastpath or div_slowpath
            )
            ref_input, ctxmgr = sample.input, nullcontext()
            if inplace:
                with torch.no_grad():
                    ref_input = [t.detach().clone() for t in sample.input]
                ctxmgr = InplaceForeachVersionBumpCheck(self, sample.input)
            try:
                with ctxmgr:
                    actual = func(
                        [sample.input, *sample.args],
                        self.is_cuda,
                        expect_fastpath,
                        **sample.kwargs,
                    )
            except Exception as e:
                with self.assertRaises(type(e)):
                    ref([ref_input, *sample.ref_args], **ref_kwargs)
            else:
                expected = ref([ref_input, *sample.ref_args], **ref_kwargs)
                self.assertEqual(expected, actual)