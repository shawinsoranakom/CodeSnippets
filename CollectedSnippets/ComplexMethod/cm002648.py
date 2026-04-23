def to(self, *args, **kwargs) -> "BatchFeature":
        """
        Send all values to device by calling `v.to(*args, **kwargs)` (PyTorch only). This should support casting in
        different `dtypes` and sending the `BatchFeature` to a different `device`.

        Args:
            args (`Tuple`):
                Will be passed to the `to(...)` function of the tensors.
            kwargs (`Dict`, *optional*):
                Will be passed to the `to(...)` function of the tensors.
                To enable asynchronous data transfer, set the `non_blocking` flag in `kwargs` (defaults to `False`).

        Returns:
            [`BatchFeature`]: The same instance after modification.
        """
        requires_backends(self, ["torch"])
        import torch

        device = kwargs.get("device")
        non_blocking = kwargs.get("non_blocking", False)
        # Check if the args are a device or a dtype
        if device is None and len(args) > 0:
            # device should be always the first argument
            arg = args[0]
            if is_torch_dtype(arg):
                # The first argument is a dtype
                pass
            elif isinstance(arg, str) or is_torch_device(arg) or isinstance(arg, int):
                device = arg
            else:
                # it's something else
                raise ValueError(f"Attempting to cast a BatchFeature to type {str(arg)}. This is not supported.")

        # We cast only floating point tensors to avoid issues with tokenizers casting `LongTensor` to `FloatTensor`
        def maybe_to(v):
            # check if v is a floating point tensor
            if isinstance(v, torch.Tensor) and torch.is_floating_point(v):
                # cast and send to device
                return v.to(*args, **kwargs)
            elif isinstance(v, torch.Tensor) and device is not None:
                return v.to(device=device, non_blocking=non_blocking)
            # recursively handle lists and tuples
            elif isinstance(v, (list, tuple)):
                return type(v)(maybe_to(item) for item in v)
            else:
                return v

        self.data = {k: maybe_to(v) for k, v in self.items()}
        return self