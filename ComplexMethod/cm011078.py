def _replace_grad_tensors(
    output: Any, tensor_iter: Iterator[torch.Tensor], _depth: int = 0
) -> Any:
    # Branch order must mirror _collect_grad_tensors exactly.
    if _depth >= _MAX_TRAVERSE_DEPTH:
        raise RuntimeError(
            f"replace_grad_tensors exceeded max depth ({_MAX_TRAVERSE_DEPTH}), "
            "likely due to a circular reference in the output structure"
        )
    if torch.is_tensor(output) and output.requires_grad:
        return next(tensor_iter)
    elif _is_namedtuple(output):
        # NamedTuple before dataclass: a NamedTuple that is also a dataclass
        # should be reconstructed via positional args, not dataclasses.replace.
        new_items = []
        any_changed = False
        for item in output:
            new_item = _replace_grad_tensors(item, tensor_iter, _depth + 1)
            new_items.append(new_item)
            if new_item is not item:
                any_changed = True
        if any_changed:
            return type(output)(*new_items)
        return output
    elif dataclasses.is_dataclass(output) and not isinstance(output, type):
        changes = {}
        for field in dataclasses.fields(output):
            old_val = getattr(output, field.name)
            new_val = _replace_grad_tensors(old_val, tensor_iter, _depth + 1)
            if new_val is not old_val:
                changes[field.name] = new_val
        if changes:
            try:
                return dataclasses.replace(output, **changes)
            except TypeError as e:
                raise TypeError(
                    f"Failed to reconstruct dataclass {type(output).__qualname__} "
                    f"via dataclasses.replace(). Dataclasses used as FSDP module "
                    f"inputs/outputs must support dataclasses.replace(): {e}"
                ) from None
        return output
    elif isinstance(output, dict):
        new_dict = {}
        any_changed = False
        for k, v in output.items():
            new_v = _replace_grad_tensors(v, tensor_iter, _depth + 1)
            new_dict[k] = new_v
            if new_v is not v:
                any_changed = True
        if any_changed:
            return new_dict if type(output) is dict else type(output)(new_dict)
        return output
    elif isinstance(output, (list, tuple)):
        new_items = []
        any_changed = False
        for item in output:
            new_item = _replace_grad_tensors(item, tensor_iter, _depth + 1)
            new_items.append(new_item)
            if new_item is not item:
                any_changed = True
        if any_changed:
            typ = type(output)
            try:
                return typ(new_items)
            except TypeError:
                # Fall back to base type for subclasses with custom __init__
                return list(new_items) if isinstance(output, list) else tuple(new_items)
        return output
    else:
        return output