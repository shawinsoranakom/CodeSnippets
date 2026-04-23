def validator(value: Union[Sequence["torch.Tensor"], "torch.Tensor"]):
        if value is None:
            return
        elif not isinstance(value, (list, tuple)):
            value = [value]
        elif isinstance(length, int) and len(value) != length:
            raise ValueError(f"Value has to be a list of length={length} but got {len(value)}")

        dimensions = {}
        for tensor in value:
            # Ensures that `value` is a floating point tensor in any device (cpu, cuda, xpu, ...).
            # Using `torch.FloatTensor` as a type hint is discouraged if the dataclass has a `strict`
            # decorator, because it enforces floating tensors only on CPU.
            if not (isinstance(tensor, torch.Tensor) and tensor.is_floating_point()):
                raise ValueError(f"Value has to be a floating point tensor but got value={tensor}")

            if len(tensor.shape) != len(shape):
                raise ValueError(f"Expected shape {shape}, but got {tensor.shape}")
            for dim, expected in zip(tensor.shape, shape):
                if isinstance(expected, int) and dim != expected:
                    raise ValueError(f"Expected dimension {expected}, but got {dim}")
                elif isinstance(expected, str):
                    if expected not in dimensions:
                        dimensions[expected] = dim
                    elif dimensions[expected] != dim:
                        raise ValueError(
                            f"Dimension '{expected}' takes different values: {dimensions[expected]} and {dim}."
                            " Please check your tensors shapes."
                        )