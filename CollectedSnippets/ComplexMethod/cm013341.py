def sample_inputs_matmul(
    op_info, device, dtype, requires_grad, op_kwargs=None, **kwargs
):
    # also run bmm samples through
    for sample_input in sample_inputs_bmm(op_info, device, dtype, requires_grad):
        # change arg name from mat2 -> other
        other = sample_input.kwargs["mat2"]
        del sample_input.kwargs["mat2"]
        sample_input.kwargs["other"] = other
        yield sample_input

    # 3D cases not covered by bmm
    for njt_3d in _sample_njts(
        device=device, dtype=dtype, requires_grad=requires_grad, dims=[3]
    ):
        # (B, j1, D) x (D, E) => (B, j1, E)
        if njt_3d._ragged_idx == 1:
            D = njt_3d.shape[-1]
            E = D + 2
            njt_desc = _describe_njt(njt_3d)
            yield SampleInput(
                _clone(njt_3d),
                kwargs={"other": torch.randn(D, E, device=device, dtype=dtype)},
                name=f"{njt_desc}: (B, j, D) x (D, E)",
            )

    # 4D cases
    for njt_4d in _sample_njts(
        device=device, dtype=dtype, requires_grad=requires_grad, dims=[4]
    ):
        # (B, j1, D, E) x (E, F) => (B, j1, D, F)
        if njt_4d._ragged_idx == 1:
            E = njt_4d.shape[-1]
            F = E + 2
            njt_desc = _describe_njt(njt_4d)
            yield SampleInput(
                _clone(njt_4d),
                kwargs={"other": torch.randn(E, F, device=device, dtype=dtype)},
                name=f"{njt_desc}: (B, j, D, E) x (E, F)",
            )

    # Dense x NJT cases
    for njt_3d in _sample_njts(
        device=device,
        dtype=dtype,
        requires_grad=requires_grad,
        dims=[3],
    ):
        # (B, F, E) x (B, E, j1) => (B, F, j1)
        if njt_3d._ragged_idx == 2:
            B = njt_3d.shape[0]
            E = njt_3d.shape[1]
            F = E + 2
            njt_desc = _describe_njt(njt_3d)
            dense_t = torch.randn(
                B, F, E, device=device, dtype=dtype, requires_grad=requires_grad
            )
            dense_t._batch_dim = 0  # for unbind_reference()
            yield SampleInput(
                dense_t,
                args=(_clone(njt_3d),),
                name=f"{njt_desc}: (B, F, E) x (B, E, j1)",
            )

    # NJT x NJT => Dense case
    for njt_3d in _sample_njts(
        device=device,
        dtype=dtype,
        requires_grad=requires_grad,
        dims=[3],
    ):
        # (B, E, j1) x (B, j1, F) => (B, E, F)
        if njt_3d._ragged_idx == 2 and njt_3d.is_contiguous():
            B, E, _ = njt_3d.shape
            sum_j1 = len(njt_3d.values())
            other_cont = torch.randn(
                sum_j1, E + 2, device=device, dtype=dtype, requires_grad=requires_grad
            )
            other_njt = torch.nested.nested_tensor_from_jagged(
                other_cont, njt_3d.offsets(), lengths=njt_3d._lengths
            )
            njt_desc = _describe_njt(njt_3d)
            yield SampleInput(
                _clone(njt_3d),
                kwargs={"other": _clone(other_njt)},
                name=f"{njt_desc}: (B, E, j1) x (B, j1, F)",
            )