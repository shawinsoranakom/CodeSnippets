def _move_missing_keys_from_meta_to_device(
        self,
        missing_keys: list[str],
        device_map: dict | None,
        device_mesh: "torch.distributed.device_mesh.DeviceMesh | None",
        hf_quantizer: HfQuantizer | None,
    ) -> None:
        """Move the missing keys (keys that are part of the model parameters, but were NOT found in the loaded state dicts)
        back from meta device to their device according to the `device_map` if any, else cpu. Takes care of sharding those
        missing parameters if `device_mesh` is provided, i.e. we are using TP.
        All non-persistent buffers are also moved back to the correct device (they are not part of the state_dict, but are
        not missing either).
        """
        is_quantized = hf_quantizer is not None
        # This is the only case where we do not initialize the model on meta device, so we don't have to do anything here
        if is_deepspeed_zero3_enabled() and not is_quantized:
            return

        # In this case we need to move everything back
        if is_fsdp_enabled() and not is_local_dist_rank_0() and not is_quantized:
            for key, param in self.named_parameters():
                value = torch.zeros_like(param, device="cpu")
                _load_parameter_into_model(self, key, value)
            for key, buffer in self.named_buffers():
                value = torch.zeros_like(buffer, device="cpu")
                _load_parameter_into_model(self, key, value)
            return

        # The tied weight keys are in the "missing" usually, but they should not be moved (they will be tied anyway)
        # This is especially important because if they are moved, they will lose the `_is_hf_initialized` flag, and they
        # will be re-initialized for nothing (which can be quite long)
        for key in missing_keys - self.all_tied_weights_keys.keys():
            param = self.get_parameter_or_buffer(key)
            param_device = get_device(device_map, key, valid_torch_device=True)
            value = torch.empty_like(param, device=param_device)
            # For TP, we may need to shard the param
            if device_mesh is not None:
                shard_and_distribute_module(
                    self, value, param, key, None, False, device_mesh.get_local_rank(), device_mesh
                )
            # Otherwise, just move it to device
            else:
                _load_parameter_into_model(self, key, value)
        # We need to move back non-persistent buffers as well, as they are not part of loaded weights anyway
        for key, buffer in self.named_non_persistent_buffers():
            buffer_device = get_device(device_map, key, valid_torch_device=True)
            value = torch.empty_like(buffer, device=buffer_device)
            _load_parameter_into_model(self, key, value)