def _test_unary_binary_equality(self, device, dtype, op, layout=torch.strided):
        samples = op.sample_inputs(device, dtype, requires_grad=True)

        for sample in samples:
            input = sample.input
            sample_args, sample_kwargs = sample.args, sample.kwargs
            mask = (
                _create_random_mask(input.shape, device)
                if "mask" not in sample_kwargs
                else sample_kwargs.pop("mask")
            )

            if layout == torch.sparse_coo:
                mask = mask.to_sparse_coo().coalesce()
                input = input.sparse_mask(mask)
            elif layout == torch.sparse_csr:
                if input.ndim != 2 or mask.ndim != 2:
                    continue
                mask = mask.to_sparse_csr()
                input = input.sparse_mask(mask)

            # Binary operations currently only support same size masks
            if is_binary(op):
                if input.shape != sample_args[0].shape:
                    continue
                # Binary operations also don't support kwargs right now
                else:
                    sample_kwargs = {}

            mt = masked_tensor(input, mask)
            mt_args = self._convert_mt_args(sample_args, mask, layout)

            mt_result = op(mt, *mt_args, **sample_kwargs)
            t_result = op(sample.input, *sample_args, **sample_kwargs)

            _compare_mt_t(mt_result, t_result)

            # If the operation is binary, check that lhs = masked, rhs = regular tensor also works
            if is_binary(op) and layout == torch.strided:
                mt_result2 = op(mt, *sample_args, **sample_kwargs)
                _compare_mt_t(mt_result2, t_result)