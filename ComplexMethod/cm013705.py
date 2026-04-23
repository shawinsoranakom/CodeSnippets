def _register_delay_all_reduce_hook(
        self,
        bucket_cap_mb,
        param_to_hook_all_reduce,
        device_ids,
    ):
        # 1. Create gradient buffer
        device = torch.device("cpu") if device_ids is None else device_ids[0]
        self._delay_grad_buffer = torch.zeros(
            sum(p.numel() for p in self._delay_all_reduce_params),
            device=device,
        )

        # 2. Broadcast the parameters
        detached_params = [p.detach() for p in self._delay_all_reduce_params]
        dist._broadcast_coalesced(self.process_group, detached_params, bucket_cap_mb, 0)

        # 3. Hook all reduce to the specified parameter
        param_to_hook_all_reduce.register_hook(self._delayed_all_reduce_hook)

        # 4. Build tensor views for gradients
        offset = 0
        for param in self._delay_all_reduce_params:
            grad_view = self._delay_grad_buffer[offset : (offset + param.numel())].view(
                param.shape
            )
            self._delay_grad_views.append(grad_view)
            offset = offset + param.numel()

        # 5. Check whether the all reduce of all params requiring grad is delayed.
        for module_name, module in self.module.named_modules():
            for param_name, param in module.named_parameters(recurse=False):
                if param.requires_grad:
                    full_name = f"{module_name}.{param_name}"
                    if full_name not in self.parameters_to_ignore:
                        # There is at least a param whose all reduce will not be delayed.
                        # In this case, we should not set self._delay_all_reduce_all_params
                        # to True.
                        return
        self._delay_all_reduce_all_params = True