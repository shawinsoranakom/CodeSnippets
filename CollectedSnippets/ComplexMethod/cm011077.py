def _collect_grad_tensors(
    output: Any, out: list[torch.Tensor], _depth: int = 0
) -> None:
    """Collect grad-requiring tensors in the same order as _replace_grad_tensors."""
    if _depth >= _MAX_TRAVERSE_DEPTH:
        raise RuntimeError(
            f"collect_grad_tensors exceeded max depth ({_MAX_TRAVERSE_DEPTH}), "
            "likely due to a circular reference in the output structure"
        )
    # Branch order must mirror _replace_grad_tensors exactly.
    # Only dict, list, tuple, NamedTuple, and dataclass are traversed;
    # set and other iterables are intentionally skipped (matching tree_flatten).
    if torch.is_tensor(output) and output.requires_grad:
        out.append(output)
    elif _is_namedtuple(output):
        # NamedTuple before dataclass to match _replace_grad_tensors ordering.
        for item in output:
            _collect_grad_tensors(item, out, _depth + 1)
    elif dataclasses.is_dataclass(output) and not isinstance(output, type):
        for field in dataclasses.fields(output):
            _collect_grad_tensors(getattr(output, field.name), out, _depth + 1)
    elif isinstance(output, dict):
        for v in output.values():
            _collect_grad_tensors(v, out, _depth + 1)
    elif isinstance(output, (list, tuple)):
        for item in output:
            _collect_grad_tensors(item, out, _depth + 1)