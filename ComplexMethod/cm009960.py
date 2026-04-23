def extractIndices(index: Any, indices: list) -> bool:
    if isinstance(index, tuple):  # mpy::tuple_view::check
        indices.extend(index)
        return True
    elif isinstance(index, torch.Tensor):  # THPVariable_Check
        indices.append(index)
        return False
    elif not hasattr(index, "__iter__") or isinstance(
        index, (str, bytes)
    ):  # !mpy::is_sequence
        indices.append(index)
        return False

    # Handle sequence case (list)
    if isinstance(index, list):
        if len(index) >= 32:
            indices.extend(index)
            return True

        # Check each item in the sequence
        for item in index:
            if (
                isinstance(item, (torch.Tensor, slice))
                or hasattr(item, "__iter__")
                or item is ...
                or item is None
                or has_dims(item)
            ):
                indices.extend(index)
                return True

        # If we got here, treat as single index
        indices.append(index)
        return False

    # Default case
    indices.append(index)
    return False