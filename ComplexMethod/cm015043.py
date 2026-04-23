def test_consistency(self, layout, device, dtype, op):
        """Checks that the op on a strided and on a sparse tensors will
        produce the same results.
        """
        if not op.supports_sparse_layout(layout):
            self.skipTest(f"{op.name} does not support input with {layout} layout")

        # FIXME: remove in followup once integer support is landed for segment_reduce
        if (layout == torch.sparse_csr and not dtype.is_floating_point
                and op.name in ('masked.mean', 'masked.amax', 'masked.amin')):
            self.skipTest(f"{op.name} does not support input with {layout} layout and {dtype} dtype")

        require_mask = isinstance(op, ReductionOpInfo) and 'masked.' in op.name

        samples = []
        for sample in op.sample_inputs(device, dtype):
            if sample.input.ndim < 2:
                continue
            dense_dim = sample.input.ndim - 2
            blocksize = (tuple(map(self._smallest_divisor, sample.input.shape[:2]))
                         if layout in {torch.sparse_bsr, torch.sparse_bsc} else None)

            def _to_sparse(x):
                if isinstance(x, torch.Tensor):
                    if blocksize is None:
                        if x.ndim != sample.input.ndim:
                            return x
                    elif x.ndim != sample.input.ndim + 2 or x.shape[-3] % blocksize[0] or x.shape[-2] % blocksize[1]:
                        return x
                    return x.clone().to_sparse(layout=layout, blocksize=blocksize, dense_dim=dense_dim)
                return x

            sparse_sample = sample.transform(_to_sparse)
            # Some strided samples (with inf, nan elements) appear to share
            # storage, so we must clone:
            sample = sample.transform(lambda x: (x.clone() if isinstance(x, torch.Tensor) else x))

            if validate_sample_input_sparse(op, sparse_sample, check_validate=False) is not sparse_sample:
                # that is, the validation returns the sparse sample
                # wrapped within ErrorInput instance
                continue
            samples.append((sample, sparse_sample))

        # Fail early to prevent silent success with this test
        if len(samples) == 0:
            raise ValueError("Expected at least one 2 or higher D tensor in samples.")

        # Re-define atol and rtol for operations that result values
        # are random (and hence, non-comparable) be we still want to
        # check the shape, dtype, etc attributes of the results:
        atol = rtol = None
        if op.name == 'randn_like':
            atol = 1e300
            rtol = 1

        for sample, sparse_sample in samples:
            expected = op(sample.input, *sample.args, **sample.kwargs)
            if not torch.is_tensor(expected):
                raise AssertionError(f"expected tensor, got {type(expected)}")
            output = op(sparse_sample.input, *sparse_sample.args, **sparse_sample.kwargs)
            if not torch.is_tensor(output):
                raise AssertionError(f"expected tensor, got {type(output)}")
            strided_output = output.to_dense()
            if require_mask and sample.kwargs.get('mask') is not None:
                output_mask = torch.masked._output_mask(op.op, sample.input, *sample.args, **sample.kwargs)
                expected.masked_fill_(~output_mask, 0)
            self.assertEqual(strided_output, expected, atol=atol, rtol=rtol)