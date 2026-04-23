def tensor_func(
        obj: torch.Tensor,
        pg: dist.ProcessGroup | None,
        device: torch.device | None,
        _: Any,
    ) -> torch.Tensor:
        if len(obj.size()) == 0:
            return torch.tensor(0, dtype=obj.dtype)

        # sometimes, a tensor might have non-zero size and 0 numel. In this case, pinning memory will fail
        # so we take a best guess at how to replicate the tensor below to maintain symmetry in the returned
        # state dict.
        if obj.numel() == 0 or obj.data_ptr() == 0:
            t = torch.zeros_like(obj, device="cpu")
            if share_memory:
                t = t.share_memory_()
            return t

        if share_memory:
            t = torch.empty(*tuple(obj.size()), dtype=obj.dtype)
            t = t.share_memory_()
            if pin_memory:
                pin_memory_utils.pin_memory(t.data_ptr(), t.numel() * t.element_size())
                weakref.finalize(t, pin_memory_utils.unpin_memory, t.data_ptr())

            return t
        elif pin_memory:
            return torch.empty(*tuple(obj.size()), dtype=obj.dtype).pin_memory()
        else:
            return torch.empty(*tuple(obj.size()), dtype=obj.dtype)