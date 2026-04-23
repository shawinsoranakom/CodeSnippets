def _track_module_params_and_buffers(
        self, module: nn.Module, install_grad_hooks: bool = True
    ) -> tuple[int, int]:
        # Track the parameters and buffers of the module if not already tracked.
        # If the parameters have gradients, track the gradients as well.
        # If install_grad_hooks is True, install a gradient hook on the parameters
        #  to track the gradients, if it has not already been installed.
        # Return the total memory consumed by the parameters and buffers.
        def _grad_hook(grad: torch.Tensor) -> None:
            self._update_and_maybe_create_winfos(
                grad,
                _MemRefType.GRAD,
            )

        param_memory = 0
        for param in module.parameters():
            winfos = self._update_and_maybe_create_winfos(
                param,
                _MemRefType.PARAM,
            )
            param_memory += sum(winfo.mem_consumed for winfo in winfos)
            if param.grad is not None:
                self._update_and_maybe_create_winfos(
                    param.grad,
                    _MemRefType.GRAD,
                )
            if (
                self._param_to_grad_hook_handles.get(param, None) is None
                and install_grad_hooks
            ):
                grad_hook_handle = param.register_hook(_grad_hook)
                post_acc_grad_hook_handle = param.register_post_accumulate_grad_hook(
                    lambda p: (_grad_hook(p.grad))
                )
                self._param_to_grad_hook_handles[param] = (
                    grad_hook_handle,
                    post_acc_grad_hook_handle,
                )
        buffer_memory = 0
        for buffer in module.buffers():
            winfos = self._update_and_maybe_create_winfos(
                buffer,
                _MemRefType.BUFFER,
            )
            buffer_memory += sum(winfo.mem_consumed for winfo in winfos)
        return (param_memory, buffer_memory)