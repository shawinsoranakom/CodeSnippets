def _unscale_grads_(
        self,
        optimizer: torch.optim.Optimizer,
        inv_scale: torch.Tensor,
        found_inf: torch.Tensor,
        allow_fp16: bool = True,
    ) -> dict[torch.device, torch.Tensor]:
        per_device_inv_scale = _GeneralMultiDeviceReplicator(inv_scale)
        per_device_found_inf = _GeneralMultiDeviceReplicator(found_inf)

        # To set up _amp_foreach_non_finite_check_and_unscale_, split grads by device and dtype.
        # There could be thousands of grads, so we'd like to iterate through them just once.
        # However, we don't know their devices or dtypes in advance.

        # https://stackoverflow.com/questions/5029934/defaultdict-of-defaultdict
        # Google says mypy struggles with defaultdicts type annotations.
        per_device_and_dtype_grads = defaultdict(lambda: defaultdict(list))  # type: ignore[var-annotated]
        with torch.no_grad():
            for group in optimizer.param_groups:
                for param in group["params"]:
                    if param.grad is None:
                        continue
                    if (not allow_fp16) and param.grad.dtype == torch.float16:
                        raise ValueError("Attempting to unscale FP16 gradients.")
                    if param.grad.is_sparse:
                        # is_coalesced() == False means the sparse grad has values with duplicate indices.
                        # coalesce() deduplicates indices and adds all values that have the same index.
                        # For scaled fp16 values, there's a good chance coalescing will cause overflow,
                        # so we should check the coalesced _values().
                        if param.grad.dtype is torch.float16:
                            # coalesce is not supported in torch.float16
                            param_grad_fp32 = param.grad.type(torch.float32).coalesce()
                            param.grad = param_grad_fp32.type(torch.float16)
                        to_unscale = param.grad._values()
                    else:
                        to_unscale = param.grad

                    per_device_and_dtype_grads[to_unscale.device][
                        to_unscale.dtype
                    ].append(to_unscale)

            for device, per_dtype_grads in per_device_and_dtype_grads.items():
                for grads in per_dtype_grads.values():
                    torch._amp_foreach_non_finite_check_and_unscale_(
                        grads,
                        per_device_found_inf.get(device),
                        per_device_inv_scale.get(device),
                    )
        # There exist contexts (e.g. w/ `use_orig_params=True`) wherein some
        # ranks may have no (non-zero sized) parameter shards, necessitating the
        # initialization of `per_device_found_inf._per_device_tensors` here
        if not per_device_found_inf._per_device_tensors:
            if self._scale is None:
                raise AssertionError("Expected _scale to be initialized, got None")
            per_device_found_inf.get(self._scale.device)
        return per_device_found_inf._per_device_tensors