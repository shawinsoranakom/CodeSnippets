def sample_inputs_sparse_csr_masked_reduction(
    op_info, device, dtype, requires_grad, **kwargs
):
    """Sample inputs for masked reduction operators that support inputs
    with sparse csr layouts.
    """
    if op_info.supports_sparse_csr:
        op_name = op_info.name.replace("masked.", "")
        for sample_input in sample_inputs_masked_reduction(
            op_info, device, dtype, requires_grad, **kwargs
        ):
            if not (
                sample_input.input.ndim == 2 and sample_input.kwargs.get("keepdim")
            ):
                # - sparse CSR tensors are always 2-D tensors
                # - masked reduction on CSR tensors are defined only if keepdim is True.
                continue
            mask = sample_input.kwargs.get("mask")
            if mask is not None:
                sample_input_kwargs = sample_input.kwargs.copy()
                sample_input_kwargs.update(mask=mask.to_sparse_csr())
                new_sample = SampleInput(
                    sample_input.input.to_sparse_csr(),
                    args=sample_input.args,
                    kwargs=sample_input_kwargs,
                )
            else:
                if op_name in ["prod", "amax", "amin", "mean"]:
                    # reductions with non-zero reduction identity and
                    # unspecified mask is not supported for sparse CSR
                    # tensors, see torch.masked.prod implementation
                    # for details.
                    continue
                new_sample = SampleInput(
                    sample_input.input.to_sparse_csr(),
                    args=sample_input.args,
                    kwargs=sample_input.kwargs,
                )
            yield new_sample
            if sample_input.kwargs["dim"] == 0:
                # Reductions of CSR tensors use different implementations for
                # inner and/or outer dimensions. So, as a minimum of testing CSR
                # implementations the following kwargs must be generated:
                #   dict(dim=0, keepdim=True)
                #   dict(dim=1, keepdim=True)
                #   dict(dim=(0, 1), keepdim=True)
                # Here we generate the dim=1 case from the dim=0 case.
                sample_input_kwargs = new_sample.kwargs.copy()
                sample_input_kwargs.update(dim=1)
                yield SampleInput(
                    new_sample.input.clone(),
                    args=sample_input.args,
                    kwargs=sample_input_kwargs,
                )