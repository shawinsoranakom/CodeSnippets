def test_python_ref_meta(self, device, dtype, op):
        CHECK_CONJ_SKIPS = {
            torch._refs.linalg.svd,
        }

        with FakeTensorMode() as mode:
            pass

        def _to_tensormeta(x):
            if isinstance(x, torch.Tensor):
                out = FakeTensor.from_tensor(x, mode)
                return out
            return x

        # TODO: iterate over requires_grad true/false
        for sample in op.reference_inputs(device, dtype, requires_grad=False):
            result = op(sample.input, *sample.args, **sample.kwargs)

            meta_sample = sample.transform(_to_tensormeta)
            try:
                with mode:
                    meta_result = op(
                        meta_sample.input, *meta_sample.args, **meta_sample.kwargs
                    )
            except torch._subclasses.fake_tensor.UnsupportedFakeTensorException:
                continue
            except torch._subclasses.fake_tensor.DataDependentOutputException:
                continue
            except torch._subclasses.fake_tensor.UnsupportedOperatorException:
                continue

            if isinstance(result, torch.Tensor):
                self.assertTrue(isinstance(meta_result, FakeTensor))
                prims.utils.compare_tensor_meta(
                    result, meta_result, check_conj=op.op not in CHECK_CONJ_SKIPS
                )
            elif isinstance(result, Sequence):
                for a, b in zip(result, meta_result):
                    if isinstance(a, torch.Tensor) or isinstance(b, torch.Tensor):
                        self.assertTrue(isinstance(b, FakeTensor))
                        prims.utils.compare_tensor_meta(
                            a, b, check_conj=op.op not in CHECK_CONJ_SKIPS
                        )