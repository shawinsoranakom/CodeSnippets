def _test_reduction_equality(self, device, dtype, op, layout=torch.strided):
        samples = op.sample_inputs(device, dtype, requires_grad=True)

        for sample in samples:
            input = sample.input
            # Reduction operations don't support more advanced args/kwargs right now
            sample_args, sample_kwargs = (), {}

            if input.dim() == 0 or input.numel() == 0:
                continue

            mask = _create_random_mask(input.shape, device)

            if torch.count_nonzero(mask) == 0:
                continue

            tensor_input = _combine_input_and_mask(op.op, input, mask)
            if layout == torch.sparse_coo:
                mask = mask.to_sparse_coo().coalesce()
                input = input.sparse_mask(mask)
            elif layout == torch.sparse_csr:
                if input.ndim != 2 or mask.ndim != 2:
                    continue
                mask = mask.to_sparse_csr()
                input = input.sparse_mask(mask)

            mt = masked_tensor(input, mask)
            mt_args = self._convert_mt_args(sample_args, mask, layout)

            mt_result = op(mt, *mt_args, **sample_kwargs)
            t_result = op(tensor_input, *sample_args, **sample_kwargs)

            _compare_mt_t(mt_result, t_result)