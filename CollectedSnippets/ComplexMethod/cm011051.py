def apply_scale(val: torch.Tensor | Iterable[torch.Tensor]):
            if isinstance(val, torch.Tensor):
                if not _is_supported_device(val):
                    raise AssertionError(f"Expected supported device, got {val.device}")
                if len(stash) == 0:
                    if self._scale is None:
                        self._lazy_init_scale_growth_tracker(val.device)
                    if self._scale is None:
                        raise AssertionError(
                            "Expected _scale to be initialized, got None"
                        )
                    stash.append(_GeneralMultiDeviceReplicator(self._scale))
                scaled_val = val * stash[0].get(val.device)
                # Here we ensure the return dtype is the same as the outputs dtype.
                # For the FSDP + Mixed Precision use case, the loss output is in the Mixed Precision
                # format (fp16, bf16) and so the scaled loss should be of the same dtype.
                return scaled_val.type(val.dtype)
            if isinstance(val, abc.Iterable):
                iterator = map(apply_scale, val)
                if isinstance(val, (list, tuple)):
                    return type(val)(iterator)
                return iterator
            raise ValueError("outputs must be a Tensor or an iterable of Tensors")