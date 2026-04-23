def all_gather_inputs(self) -> list[torch.Tensor]:  # 1D
        self._assert_in_states(ShardedState.SHARDED, ShardedState.SHARDED_POST_FORWARD)
        if self.sharded_state == ShardedState.SHARDED:
            if hasattr(self._sharded_local_tensor, "fsdp_pre_all_gather"):
                sharded_local_tensor = self._sharded_local_tensor
                if self.offload_to_cpu:
                    sharded_local_tensor = sharded_local_tensor.to(
                        self.device, non_blocking=True
                    )
                pre_all_gather_signature = inspect.signature(
                    # pyrefly: ignore [missing-attribute]
                    sharded_local_tensor.fsdp_pre_all_gather
                )
                num_fn_params = len(pre_all_gather_signature.parameters)
                # Old signature only passes mesh; keep for BC for now
                if num_fn_params not in (1, 5):
                    raise AssertionError(
                        f"Invalid fsdp_pre_all_gather: {pre_all_gather_signature}\n"
                        "Expects fsdp_pre_all_gather(self, mesh: DeviceMesh, "
                        "outer_size: torch.Size, outer_stride: tuple[int, ...], "
                        "module: nn.Module, mp_policy: MixedPrecisionPolicy)"
                    )
                if num_fn_params == 1:
                    (
                        all_gather_inputs,
                        self._extensions_data.all_gather_metadata,
                        # pyrefly: ignore [missing-attribute]
                    ) = sharded_local_tensor.fsdp_pre_all_gather(
                        self.shard_mesh_from_root
                    )
                else:
                    (
                        all_gather_inputs,
                        self._extensions_data.all_gather_metadata,
                        # pyrefly: ignore [missing-attribute]
                    ) = sharded_local_tensor.fsdp_pre_all_gather(
                        self.shard_mesh_from_root,
                        self._orig_size,
                        self._contiguous_orig_stride,
                        self._module_info.module,
                        self.mp_policy,
                    )
                    if (
                        sharded_local_tensor.size() != self.padded_sharded_param_size
                        and any(
                            all_gather_input.size() != self.padded_sharded_param_size
                            for all_gather_input in all_gather_inputs
                        )
                    ):
                        # NOTE: Since this error can only be raised on the
                        # ranks that have padding, this can manifest as a NCCL
                        # watchdog timeout, as the other ranks will not error.
                        raise AssertionError(
                            "When a parameter is unevenly sharded by FSDP "
                            f"(orig size={self._orig_size}, FSDP world size={self.mesh_info.mesh.size()}), "
                            "fsdp_pre_all_gather must return all-gather inputs with the padded sharded size "
                            f"{self.padded_sharded_param_size} but got {[t.size() for t in all_gather_inputs]}"
                        )
                self._extensions_data.all_gather_input_sizes = [
                    t.size() for t in all_gather_inputs
                ]
                return [t.view(-1) for t in all_gather_inputs]
            sharded_param_data = self._sharded_param_data
            if self.offload_to_cpu:
                sharded_param_data = sharded_param_data.to(
                    self.device, non_blocking=True
                )
            return [_to_dtype_if_needed(sharded_param_data, self.param_dtype)]
        elif self.sharded_state == ShardedState.SHARDED_POST_FORWARD:
            if hasattr(self._sharded_local_tensor, "fsdp_pre_all_gather"):
                raise NotImplementedError
            all_gather_input = _to_dtype_if_needed(
                cast(torch.Tensor, self._sharded_post_forward_param_data),
                self.param_dtype,
            )
            return [all_gather_input]
        return [torch.empty(0)]