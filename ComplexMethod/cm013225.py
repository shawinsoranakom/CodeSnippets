def __call__(self, opinfo, device, dtype, requires_grad, **kwargs):
        num_input_tensors = kwargs.pop("num_input_tensors", foreach_num_tensors)
        if not isinstance(num_input_tensors, list):
            raise AssertionError(f"Expected num_input_tensors to be a list, got {type(num_input_tensors)}")
        _foreach_inputs_kwargs = {k: kwargs.pop(k, v) for k, v in _foreach_inputs_default_kwargs.items()}
        _foreach_inputs_kwargs["requires_grad"] = requires_grad
        _allow_higher_dtype_scalars = kwargs.pop("allow_higher_dtype_scalars", False)

        for num_tensors, ord, out_dtype, intersperse_empty_tensors in product(
            num_input_tensors,
            (0, 1, 2, -1, -2, float('inf'), float('-inf')),
            (None,) + (highest_precision_complex(device),) if dtype in complex_types() else (highest_precision_float(device),),
            (True, False),
        ):
            # inf norm and negative norms on empty tensors is not supported by our reference func vector norm:
            # linalg.vector_norm cannot compute the inf norm on an empty tensor because the operation does not have an identity
            if (ord in [float('inf'), float('-inf')] or ord < 0) and intersperse_empty_tensors:
                continue

            _foreach_inputs_kwargs["intersperse_empty_tensors"] = intersperse_empty_tensors
            input = sample_inputs_foreach(None, device, dtype, num_tensors, zero_size=False, **_foreach_inputs_kwargs)
            disable_fastpath = True
            if ord in (0, 1, 2, float('inf')) and dtype in floating_types_and(torch.half, torch.bfloat16):
                disable_fastpath = False
            yield ForeachSampleInput(input, ord=ord, disable_fastpath=disable_fastpath, dtype=out_dtype)

        # Also test nan propagation with a single tensor, but skip autograd testing
        if not requires_grad:
            nan_inputs = [
                [float('nan')],
                [float('nan'), 1.0],
                [1.0, float('nan')],
                [1.0, 2.0, 3.0, float('nan'), float('nan'), 7.0, float('nan'), float('nan'), -1.5, 6.0],
                [7.0, 3.0, float('nan'), float('nan'), -1.5, 6.0],
                [3.0, float('nan'), float('nan'), -1.5, 6.0],
            ]
            for input in nan_inputs:
                x = torch.tensor(input, device=device)
                disable_fastpath = True
                if ord in (0, 1, 2, float('inf')) and dtype in floating_types_and(torch.half, torch.bfloat16):
                    disable_fastpath = False
                yield ForeachSampleInput([x], ord=ord, disable_fastpath=disable_fastpath)