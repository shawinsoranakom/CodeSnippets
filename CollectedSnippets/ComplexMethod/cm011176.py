def _instrument_fsdp_module(self) -> None:
        # We uninstall the existing `FSDPState._pre_forward` and `FSDPState._post_forward` hooks and install
        # our own hooks that wrap them. We choose this over monkey-patching `FSDPParamGroup.pre_forward` and
        # `FSDPParamGroup.post_forward` because during AC these won't be called.
        # TODO(@sanketpurandare): This will need to be modified after this PR (https://github.com/pytorch/pytorch/pull/127786)
        # lands. For backward we monkey-patch the `FSDPParamGroup.pre_backward` and `FSDPParamGroup.post_backward`.

        # get the unique _MultiHandlers/RemoveHandlers and store in dictionary
        # the _MultiHandlers object will only need to be grabbed once.
        unique_handlers: dict[RemovableHandle, bool] = {}

        for module in self._root_mod.modules():
            if isinstance(module, FSDPModule):
                fsdp_state = module._get_fsdp_state()
                if fsdp_param_group := fsdp_state._fsdp_param_group:
                    if not unique_handlers.get(fsdp_state._pre_forward_hook_handle):
                        unique_handlers[fsdp_state._pre_forward_hook_handle] = True
                    if not unique_handlers.get(fsdp_state._post_forward_hook_handle):
                        unique_handlers[fsdp_state._post_forward_hook_handle] = True
        # call remove on the handles once
        for f_hook_handle in unique_handlers:
            f_hook_handle.remove()

        for module in self._root_mod.modules():
            if isinstance(module, FSDPModule):
                fsdp_state = module._get_fsdp_state()
                if fsdp_param_group := fsdp_state._fsdp_param_group:
                    self._instrument_fsdp_sharded_params_grads(fsdp_param_group)
                    fsdp_state._pre_forward_hook_handle = (
                        module.register_forward_pre_hook(
                            self._fsdp_state_pre_forward(
                                module, fsdp_state._pre_forward
                            ),
                            prepend=True,
                            with_kwargs=True,
                        )
                    )

                    fsdp_state._post_forward_hook_handle = module.register_forward_hook(
                        self._fsdp_state_post_forward(module, fsdp_state._post_forward),
                        prepend=False,
                        always_call=True,
                    )
                    self._fsdp_mod_to_saved_methods[module] = _SavedFSDPMethods(
                        fsdp_param_group.pre_backward,
                        fsdp_param_group.post_backward,
                    )
                    fsdp_param_group.pre_backward = self._fsdp_param_group_pre_backward(  # type: ignore[assignment]
                        module, fsdp_param_group.pre_backward
                    )
                    fsdp_param_group.post_backward = (  # type: ignore[assignment]
                        self._fsdp_param_group_post_backward(
                            module, fsdp_param_group.post_backward
                        )
                    )

        for buffer in self._root_mod.buffers():
            self._update_and_maybe_create_winfos(
                buffer,
                _FSDPRefType.BUFFER,
            )