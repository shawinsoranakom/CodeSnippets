def _to(self, device, non_blocking=False):
    """Returns a copy of this object in device memory.

    If this object is already on the correct device, then no copy is performed
    and the original object is returned.

    Args:
        device (int): The destination device.
        non_blocking (bool): If ``True`` and the source is in pinned memory,
            the copy will be asynchronous with respect to the host. Otherwise,
            the argument has no effect.
    """
    if self.device == device:
        return self

    if device.type == "cpu":
        pin_memory = non_blocking and self.device.type in (
            "cuda",
            torch._C._get_privateuse1_backend_name(),
        )
        untyped_storage = torch.empty(
            self.nbytes(), dtype=torch.uint8, device=device, pin_memory=pin_memory
        ).untyped_storage()
        untyped_storage.copy_(self, non_blocking)
        return untyped_storage

    device_module = getattr(torch, device.type, None)
    if device_module is None:
        raise AssertionError(f"{device.type.upper()} device module is not loaded")
    with device_module.device(device):
        if self.is_sparse and hasattr(device_module, "sparse"):
            new_type = getattr(device_module.sparse, self.__class__.__name__)
            indices = getattr(torch.Tensor._indices(self), device.type)(
                device, non_blocking
            )
            values = getattr(torch.Tensor._values(self), device.type)(
                device, non_blocking
            )
            return new_type(indices, values, self.size())
        else:
            if self.is_sparse:
                raise AssertionError(
                    f"sparse storage is not supported for {device.type.upper()} tensors"
                )
            untyped_storage = torch.UntypedStorage(self.size(), device=device)
            untyped_storage.copy_(self, non_blocking)
            return untyped_storage