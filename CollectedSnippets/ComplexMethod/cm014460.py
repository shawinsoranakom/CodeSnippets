def pin_memory(data, device=None):
    if isinstance(data, torch.Tensor):
        return data.pin_memory()

    if hasattr(data, "pin_memory"):
        return data.pin_memory()

    if isinstance(data, (str, bytes)):
        return data

    if isinstance(data, collections.abc.Mapping):
        try:
            if isinstance(data, collections.abc.MutableMapping):
                # The mapping type may have extra properties, so we can't just
                # use `type(data)(...)` to create the new mapping.
                # Create a clone and update it if the mapping type is mutable.
                clone = copy.copy(data)
                clone.update(
                    {k: pin_memory(sample, device) for k, sample in data.items()}
                )
                return clone
            else:
                # pyrefly: ignore [bad-instantiation]
                return type(data)(
                    # pyrefly: ignore [bad-argument-count]
                    {k: pin_memory(sample, device) for k, sample in data.items()}
                )  # type: ignore[call-arg]
        except TypeError:
            # The mapping type may not support `copy()` / `update(mapping)`
            # or `__init__(iterable)`.
            return {k: pin_memory(sample, device) for k, sample in data.items()}

    if isinstance(data, tuple):
        if hasattr(data, "_fields"):  # namedtuple
            return type(data)(*(pin_memory(sample, device) for sample in data))
        return type(data)(pin_memory(sample, device) for sample in data)

    if isinstance(data, collections.abc.Sequence):
        try:
            if isinstance(data, collections.abc.MutableSequence):
                # The sequence type may have extra properties, so we can't just
                # use `type(data)(...)` to create the new sequence.
                # Create a clone and update it if the sequence type is mutable.
                clone = copy.copy(data)  # type: ignore[arg-type]
                for i, item in enumerate(data):
                    clone[i] = pin_memory(item, device)
                return clone
            return type(data)([pin_memory(sample, device) for sample in data])  # type: ignore[call-arg]
        except TypeError:
            # The sequence type may not support `copy()` / `__setitem__(index, item)`
            # or `__init__(iterable)` (e.g., `range`).
            return [pin_memory(sample, device) for sample in data]

    return data