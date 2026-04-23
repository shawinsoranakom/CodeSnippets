def _is_tensor_output(result: Any) -> bool:
    """Check if a result is a tensor or list/tuple of tensors."""
    if isinstance(result, torch.Tensor):
        return True
    if isinstance(result, (list, tuple)):
        has_tensor = any(isinstance(t, torch.Tensor) for t in result)
        all_tensor = all(isinstance(t, torch.Tensor) for t in result)
        if has_tensor and not all_tensor:
            raise NotImplementedError(
                f"Mixed tensor/non-tensor tuple outputs are not supported by the "
                f"validator. Got types: {[type(t).__name__ for t in result]}"
            )
        return all_tensor
    return False