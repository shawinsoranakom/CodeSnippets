def sample_inputs_njt_reduction(
    op_info,
    device,
    dtype,
    requires_grad,
    supports_keepdim=True,
    op_kwargs=None,
    **kwargs,
):
    if not op_kwargs:
        op_kwargs = {}

    # extract info about the dim args this op supports
    if op_info._extra_op_data.dim_args is None:
        raise AssertionError("Expected op_info._extra_op_data.dim_args to not be None")
    (
        single_dim_argname,
        dimlist_argname,
    ) = op_info._extra_op_data.get_dim_argnames()
    if single_dim_argname is None:
        raise AssertionError("Expected single_dim_argname to not be None")
    supports_dimlist = dimlist_argname is not None

    for njt in _sample_njts(
        device=device, dtype=dtype, requires_grad=requires_grad, dims=[2, 3, 4]
    ):
        njt_desc = _describe_njt(njt)
        keepdim_values = [False, True] if supports_keepdim else [None]
        for keepdim in keepdim_values:
            keepdim_suffix = f" with keepdim={keepdim}" if supports_keepdim else ""
            # single dim-wise reduction; includes reduction over the ragged dim
            # NB: reduction over the batch dim is not supported!
            # TODO: Cover this in the set of error inputs
            for dim in range(1, njt.dim()):
                dim_desc = "normal" if dim != njt._ragged_idx else "ragged"
                yield SampleInput(
                    _clone(njt),
                    kwargs={
                        **op_kwargs,
                        single_dim_argname: dim,
                        **({"keepdim": keepdim} if supports_keepdim else {}),
                    },
                    name=f"{njt_desc}: {dim_desc} dim reduction{keepdim_suffix}",
                )

            if supports_dimlist:
                # reduce on both batch and ragged dims
                yield SampleInput(
                    _clone(njt),
                    kwargs={
                        **op_kwargs,
                        dimlist_argname: [0, njt._ragged_idx],
                        **({"keepdim": keepdim} if supports_keepdim else {}),
                    },
                    name=f"{njt_desc}: batch+ragged reduction{keepdim_suffix}",
                )

                # reduce on batch, ragged, and other dims
                for other_dim in range(njt._ragged_idx + 1, njt.dim()):
                    yield SampleInput(
                        _clone(njt),
                        kwargs={
                            **op_kwargs,
                            dimlist_argname: [0, njt._ragged_idx, other_dim],
                            **({"keepdim": keepdim} if supports_keepdim else {}),
                        },
                        name=(
                            f"{njt_desc}: batch+ragged+dim={other_dim} "
                            f"reduction{keepdim_suffix}"
                        ),
                    )

                # reduce on two non-ragged, non-batch dims
                if njt.dim() > 3 and njt._ragged_idx == 1:
                    yield SampleInput(
                        _clone(njt),
                        kwargs={
                            **op_kwargs,
                            dimlist_argname: [njt.dim() - 2, njt.dim() - 1],
                            **({"keepdim": keepdim} if supports_keepdim else {}),
                        },
                        name=f"{njt_desc}: two normal dim reduction{keepdim_suffix}",
                    )

                # full reduction by specifying all dims
                yield SampleInput(
                    _clone(njt),
                    kwargs={
                        **op_kwargs,
                        dimlist_argname: list(range(njt.dim())),
                        **({"keepdim": keepdim} if supports_keepdim else {}),
                    },
                    name=f"{njt_desc}: all dim reduction{keepdim_suffix}",
                )

                # TODO: Reducing on ragged dim and non-batch dim is not supported;
                # cover this in the set of error inputs.

        # full reduction
        yield SampleInput(
            _clone(njt),
            kwargs=dict(op_kwargs),
            name=f"{njt_desc}: full reduction with keepdim={keepdim}",
        )