def tensor(self, name: str, t: torch.Tensor) -> None:
        from torch.fx.experimental.symbolic_shapes import statically_known_true, sym_eq

        storage = self.storage(
            t.untyped_storage(), dtype_hint=t.dtype, device_hint=t.device
        )
        args = []
        # NB: this is positional, must come first
        if not statically_known_true(
            sym_eq(_stride_or_default(None, shape=t.shape), t.stride())
        ):
            args.append(str(tuple(t.stride())))
        if _dtype_or_default(None) != t.dtype:
            args.append(f"dtype={t.dtype!r}")
        if not statically_known_true(
            _storage_offset_or_default(None) == t.storage_offset()
        ):
            args.append(f"storage_offset={t.storage_offset()!r}")
        tensor_metadata = torch._utils.get_tensor_metadata(t)
        if tensor_metadata:
            args.extend(f"{k}={v!r}" for k, v in tensor_metadata.items())
        if _requires_grad_or_default(None) != t.requires_grad:
            args.append(f"requires_grad={t.requires_grad!r}")
        is_leaf = torch._subclasses.meta_utils.safe_is_leaf(t)
        if _is_leaf_or_default(None) != is_leaf:
            args.append(f"is_leaf={is_leaf!r}")
        self._lines.append(
            "reader.tensor("
            + ", ".join([storage, str(tuple(t.shape)), *args])
            + f")  # {name}"
        )