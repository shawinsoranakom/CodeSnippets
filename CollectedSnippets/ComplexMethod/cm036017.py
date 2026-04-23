def _unscale_grads_(self, optimizer: Optimizer, inv_scale: torch.Tensor, found_inf: torch.Tensor,
                        allow_fp16: bool) -> Dict[torch.device, torch.Tensor]:
        per_device_inv_scale = grad_scaler._MultiDeviceReplicator(inv_scale)
        per_device_found_inf = grad_scaler._MultiDeviceReplicator(found_inf)

        per_device_and_dtype_grads = defaultdict(lambda: defaultdict(list))  # type: ignore[var-annotated]

        with torch.no_grad():
            # Loop through parameters
            for group in optimizer.param_groups:
                for param in group["params"]:
                    # Skip non-trainable parameters
                    if param.grad is None:
                        continue
                    # Not implemented for sparse tensors
                    if param.grad.is_sparse:
                        raise NotImplementedError

                    # If we are using the `AdamFP16` optimizer set `optimizer.grad_fp32[param]` to the FP32 gradients
                    if isinstance(optimizer, AdamFP16):
                        grad = param.grad.to(torch.float)
                        optimizer.grad_fp32[param] = grad
                    # Otherwise, do not convert the gradients to FP32
                    else:
                        grad = param.grad

                    per_device_and_dtype_grads[grad.device][grad.dtype].append(grad)

            # Unscale all the gradients
            for device, per_dtype_grads in per_device_and_dtype_grads.items():
                for grads in per_dtype_grads.values():
                    torch._amp_foreach_non_finite_check_and_unscale_(grads,
                                                                     per_device_found_inf.get(device),
                                                                     per_device_inv_scale.get(device))
        #
        return per_device_found_inf._per_device_tensors