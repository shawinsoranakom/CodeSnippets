def chunk_default(func, *args, **kwargs):
    _, new_kwargs = normalize_function(  # type: ignore[misc]
        func, args=args, kwargs=kwargs, normalize_to_only_use_kwargs=True
    )

    inp = new_kwargs.pop("input")

    new_kwargs["dim"], operating_on_batch = _wrap_jagged_dim(
        inp.dim(), new_kwargs["dim"], inp._ragged_idx, "chunk", allow_batch_dim=True
    )

    if operating_on_batch:
        chunks = new_kwargs["chunks"]

        # get _offsets of the chunks
        lengths = inp._offsets.diff()
        chunked_lengths = lengths.chunk(chunks)
        chunked_offsets = [torch.cumsum(x, dim=0) for x in chunked_lengths]
        chunked_offsets = [F.pad(x, (1, 0), value=0) for x in chunked_offsets]  # type: ignore[arg-type]
        nested_kwargs = [
            {"offsets": per_offsets, "_ragged_idx": inp._ragged_idx}
            for per_offsets in chunked_offsets
        ]

        # get _values of the chunks
        split_sizes = [x.sum().item() for x in chunked_lengths]
        chunk_values = inp._values.split(split_sizes)

        # Note that the actual number of chunks returned is not necessarily the same as
        # the input number; it can be counter-intuitive, but it matches dense behavior.
        return [
            NestedTensor(values=chunk_values[i], **(nested_kwargs[i]))
            for i in range(len(chunk_values))
        ]
    else:
        return [
            NestedTensor(values=x, **extract_kwargs(inp))
            for x in func(inp._values, **new_kwargs)
        ]