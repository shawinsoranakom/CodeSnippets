def masked_samples():
        for sample_input in sample_inputs_std_var(
            op_info, device, dtype, requires_grad, **kwargs
        ):
            if len(sample_input.args) and isinstance(sample_input.args[0], bool):
                continue  # masked.{std, var} doesn't support `.var(unbiased)`

            for mask in _generate_masked_op_mask(
                sample_input.input.shape, device, **kwargs
            ):
                sample_input_args, sample_input_kwargs = (
                    sample_input.args,
                    dict(mask=mask, **sample_input.kwargs),
                )
                yield SampleInput(
                    sample_input.input.detach().requires_grad_(requires_grad),
                    args=sample_input_args,
                    kwargs=sample_input_kwargs,
                )
                if (
                    not requires_grad
                    and dtype.is_floating_point
                    and sample_input.input.ndim == 2
                    and mask is not None
                    and mask.shape == sample_input.input.shape
                ):
                    for v in [torch.inf, -torch.inf, torch.nan]:
                        t = sample_input.input.detach()
                        t.diagonal(0, -2, -1).fill_(v)
                        yield SampleInput(
                            t.requires_grad_(requires_grad),
                            args=sample_input_args,
                            kwargs=sample_input_kwargs,
                        )