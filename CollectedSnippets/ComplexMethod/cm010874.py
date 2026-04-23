def coerce_tangent_and_suggest_memory_format(
    x: Tensor,
) -> tuple[Any, MemoryFormatMeta | list[Any] | None, bool]:
    updated = False
    if not isinstance(x, Tensor):
        return x, None, updated

    out = x.detach()

    is_subclass = is_traceable_wrapper_subclass(out)

    memory_format = MemoryFormatMeta.from_tensor(out)

    # pyrefly: ignore [missing-attribute]
    if memory_format.memory_format is not None:
        was = out
        # pyrefly: ignore [bad-argument-type]
        out = out.contiguous(memory_format=memory_format.memory_format)
        updated = was is not out

    # For subclass we keep memory format of outer strides at the beginning of the list
    out_memory_format = [memory_format] if is_subclass else memory_format

    # Note [Tangents memory format, Part 2]
    # In the same way that "what strides do we assigns to our tangents" is a question
    # that we can not answer (and therefore have to guess) as we trace the backward ahead-of-time,
    # The same applies to any tensor subclass metadata, when we have tangents that are subclasses.
    # To handle this situation, we have two new methods that a tensor subclass can implement:
    # (1) __coerce_tangent_metadata__(self)
    #     Given a subclass with "non-standard" metadata, turn it into a new subclass with "normal" metadata.
    #     The main example here is a DTensor with the "_Partial" placement.
    #     If we have a forward output with a _Partial placement, and corresponding tangent
    #     with a Replicate/Shard placement, we have no way to convert the tangent "back" to a _Partial placement.
    #     This method lets us avoid the problem entirely by allowing subclasses to ensure that we can never
    #     have a tangent with "problematic" metadata, that we cannot convert to.
    # (1) __coerce_same_metadata_as_tangent__(self, metadata)
    #     Given a subclass, and a target differing metadata,
    #     convert self to have the same metadata as the target.
    #     With DTensor being the main example, we can use this to convert a DTensor with a Replicate()
    #     placement into one with a Shard() placement, in the case that we "guessed wrong",
    #     and traced tangents with a Shard() placement at compile time.
    #
    if is_subclass and hasattr(out, "__coerce_tangent_metadata__"):
        out = out.__coerce_tangent_metadata__()  # type: ignore[attr-defined]

    if is_subclass:
        # pyrefly: ignore [missing-attribute]
        attrs = out.__tensor_flatten__()[0]

        for attr in attrs:
            elem = getattr(out, attr)
            (
                new_elem,
                new_elem_memory_format,
                elem_updated,
            ) = coerce_tangent_and_suggest_memory_format(elem)
            # pyrefly: ignore [missing-attribute]
            out_memory_format.append(new_elem_memory_format)
            if elem_updated:
                setattr(out, attr, new_elem)

    return out, out_memory_format, updated