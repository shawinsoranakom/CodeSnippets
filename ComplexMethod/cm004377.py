def to(self, *args, **kwargs) -> "BatchFeature":
        """
        Send all values to device by calling `v.to(*args, **kwargs)` (PyTorch only). This should support casting in
        different `dtypes` and sending the `BatchFeature` to a different `device`.

        Args:
            args (`Tuple`):
                Will be passed to the `to(...)` function of the tensors.
            kwargs (`Dict`, *optional*):
                Will be passed to the `to(...)` function of the tensors.

        Returns:
            [`BatchFeature`]: The same instance after modification.
        """
        requires_backends(self, ["torch"])
        import torch

        from ...utils import is_torch_device, is_torch_dtype

        new_data = {}
        device = kwargs.get("device")
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

        def _to(elem):
            # check if v is a floating point
            if torch.is_floating_point(elem):
                # cast and send to device
                return elem.to(*args, **kwargs)
            if device is not None:
                return elem.to(device=device)

            return elem

        # We cast only floating point tensors to avoid issues with tokenizers casting `LongTensor` to `FloatTensor`
        for k, v in self.items():
            if isinstance(v, list) and isinstance(v[0], list):
                # Data structure is a list of lists
                new_v = []
                for elems in v:
                    new_v.append([_to(elem) for elem in elems])
                new_data[k] = new_v
            elif isinstance(v, list):
                # Data structure is a list
                new_data[k] = [_to(elem) for elem in v]
            else:
                new_data[k] = _to(v)
        self.data = new_data
        return self