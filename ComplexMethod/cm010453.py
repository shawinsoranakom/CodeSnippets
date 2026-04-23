def _apply_reduction(func, func_name, identity_element, *args, **kwargs):
    _, new_kwargs = normalize_function(  # type: ignore[misc]
        func, args=args, kwargs=kwargs, normalize_to_only_use_kwargs=True
    )

    inp = new_kwargs.pop("input")

    # some ops use dim=None to indicate a full reduction; some use an empty dim list
    full_reduction = new_kwargs["dim"] is None or (
        isinstance(new_kwargs["dim"], (tuple, list)) and len(new_kwargs["dim"]) == 0
    )
    if full_reduction:
        out = func(inp._values, **new_kwargs)
        if new_kwargs.get("keepdim", False):
            if isinstance(out, (tuple, list)):
                # some ops return multiple things; unsqueeze all of them
                out = type(out)(o.unsqueeze(inp._ragged_idx) for o in out)
            else:
                out = out.unsqueeze(inp._ragged_idx)
        return out

    # some ops support lists of dims; some don't
    dim_to_convert = new_kwargs["dim"]
    is_dimlist = isinstance(new_kwargs["dim"], (tuple, list))
    if not is_dimlist:
        dim_to_convert = [dim_to_convert]

    (
        converted_dim,
        reduce_on_batch,
        reduce_on_ragged,
        reduce_on_non_batch,
    ) = _wrap_jagged_dims(
        inp.dim(),
        dim_to_convert,
        f"{func_name}",
        inp._ragged_idx,
    )

    if not is_dimlist:
        # convert back from list
        converted_dim = converted_dim[0]
    new_kwargs["dim"] = converted_dim

    if reduce_on_ragged and inp._lengths is not None:
        raise RuntimeError(
            f"{func_name}(): reducing across the ragged dimension is not supported "
            "for non-contiguous nested tensors with holes"
        )

    from torch.utils._pytree import tree_map

    # raggedness reduced away --> return dense tensor
    if reduce_on_ragged:
        # reduction cases: (batch, ragged), (batch, ragged, non-batch), etc.
        if reduce_on_batch:
            # no need to read offsets --> apply sum directly on values
            out = func(inp._values, **new_kwargs)
            if new_kwargs.get("keepdim", False):
                # some ops return multiple things; unsqueeze all of them
                out = tree_map(lambda o: o.unsqueeze(0), out)
            return out
        else:
            # invalid reduction cases: (ragged, non-batch), etc.
            if reduce_on_non_batch:
                raise RuntimeError(
                    f"{func_name}(): reducing along a ragged and non-batch dimension "
                    "is not supported for nested tensors"
                )

            # reduction cases: (ragged)
            # convert to padded dense and reduce
            new_kwargs.pop("dim")
            dim_to_pass = [inp._ragged_idx] if is_dimlist else inp._ragged_idx
            return func(
                inp.to_padded_tensor(identity_element), dim=dim_to_pass, **new_kwargs
            )
    # raggedness preserved --> return nested tensor
    else:
        # invalid reduction cases: (batch), (batch, non-batch), etc.
        if reduce_on_batch:
            raise RuntimeError(
                f"{func_name}(): reducing along the batch dimension but not "
                "the ragged dimension is not supported for nested tensors"
            )

        # reduction cases: (non-batch), (non-batch, non-batch), etc.
        # apply sum directly on values
        out = func(inp._values, **new_kwargs)
        out_kwargs = extract_kwargs(inp)
        if not new_kwargs.get("keepdim", False):
            # dims are reduced away -> ragged_idx of output needs to be reevaluated
            dimlist = (
                new_kwargs["dim"]
                if isinstance(new_kwargs["dim"], (tuple, list))
                else [new_kwargs["dim"]]
            )
            for d in dimlist:
                # adjust for all dims reduced before the ragged dim
                if d < inp._ragged_idx - 1:
                    out_kwargs["_ragged_idx"] -= 1

        # some ops return multiple things; wrap each of them as an NJT
        return tree_map(lambda o: NestedTensor(o, **out_kwargs), out)