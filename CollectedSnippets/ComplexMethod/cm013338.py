def unbind_reference(op, sample, wrap_output_as_njt=True):
    # first NJT in the arglist determines expected ragged structure
    nt_inp = (
        sample.input
        if sample.input.is_nested
        # TODO: look in kwargs too?
        else next(a for a in sample.args if a.is_nested)
    )

    out_ref_components = []
    for i in range(nt_inp.shape[0]):

        def _slice_input(t, i=i, inp=nt_inp):
            # any NJT with the same ragged structure as the input should
            # be sliced to pass to the reference
            if isinstance(t, torch.Tensor) and _raggedness_matches(t, inp):
                return t[i]
            # allow the SampleInput to tell us how to slice it for ref calculation
            elif isinstance(t, torch.Tensor) and hasattr(t, "_batch_dim"):
                bdim = t._batch_dim  # type: ignore[attr]
                if t.shape[bdim] == 1:
                    return t[0]
                else:
                    return t.select(bdim, i)
            else:
                return t

        inp = _slice_input(sample.input)
        args = tree_map(_slice_input, sample.args)
        kwargs = tree_map(_slice_input, sample.kwargs)

        # Handle indices in index_put
        if "index_put" in op.full_name and "indices" in kwargs:
            if len(kwargs["indices"]) > 1:
                # If after unrolling we still have indices left, use them
                kwargs["indices"] = [t[i] for t in kwargs["indices"][1:]]
            else:
                # If no indices are left, create them so they match the NJT implementation
                sequence_put = kwargs["indices"][0].tolist()
                if i in sequence_put:
                    kwargs["indices"] = [
                        torch.tensor(
                            list(range(inp.shape[0])),
                            dtype=torch.int32,
                            device=kwargs["indices"][0].device,
                        )
                    ]
                else:
                    kwargs["indices"] = [
                        torch.tensor(
                            [], dtype=torch.int32, device=kwargs["indices"][0].device
                        )
                    ]

        from torch.nested._internal.ops import _outer_to_inner_dim

        # Need to adjust dims to apply on NJT component
        if op._extra_op_data.dim_args is not None:
            # get all possible dim-related argnames that could be encountered for this op
            argnames = tree_map(
                lambda a: a.replace("...", ""),
                tree_flatten(op._extra_op_data.dim_args)[0],
            )
            # for all dim-related args present, convert from outer -> inner dim space
            for argname in {a for a in argnames if a in kwargs}:
                # allow the SampleInput to tell us how to canonicalize the dim kwargs
                ndim = nt_inp._ndim if hasattr(nt_inp, "_ndim") else nt_inp.dim()
                kwargs[argname] = _outer_to_inner_dim(
                    ndim, kwargs[argname], nt_inp._ragged_idx, canonicalize=True
                )

        out_ref_component = op.op(inp, *args, **kwargs)
        out_ref_components.append(out_ref_component)

    if wrap_output_as_njt:
        # handle list / tuple of outputs
        if len(out_ref_components) > 0 and isinstance(
            out_ref_components[0], (list, tuple)
        ):
            num_returns = len(out_ref_components[0])
            # ensure we get the same number of returns for each invocation
            if not all(len(o) == num_returns for o in out_ref_components):
                raise AssertionError(
                    f"Expected all outputs to have {num_returns} returns"
                )
            # construct NJTs from same index returns from each invocation
            njt_returns = [
                torch.nested.as_nested_tensor(
                    [o[r] for o in out_ref_components], layout=torch.jagged
                )
                for r in range(num_returns)
            ]
            return type(out_ref_components[0])(njt_returns)
        return torch.nested.as_nested_tensor(out_ref_components, layout=torch.jagged)

    return out_ref_components