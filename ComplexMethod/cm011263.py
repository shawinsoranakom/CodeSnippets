def _retrieve_recv_activations(
        self,
        fwd_chunk_id: int,
    ):
        """
        Retrieve the activations received for the current stage during forward.
        Reconstructs DTensors if the inputs were DTensors.
        Also validates DTensor metadata against expected values.
        """
        recv_infos = self.args_recv_info[fwd_chunk_id]

        activations = []
        for i, info in enumerate(recv_infos):
            if not info.is_root_arg:
                # Non-root args have valid buffer and tensor_meta
                if info.buffer is None or info.tensor_meta is None:
                    raise PipeliningMetadataError(
                        f"Non-root arg '{info.input_name}' has None buffer or tensor_meta"
                    )
                # Effective requires_grad: metadata captures what the model
                # produced, but the runtime context (has_backward, grad mode)
                # determines whether we actually need gradients.
                effective_requires_grad = (
                    info.tensor_meta.requires_grad
                    and self.has_backward
                    and torch.is_grad_enabled()
                )
                if isinstance(info.tensor_meta, _DTensorMeta):
                    # Buffer must not require grad so from_local stays out
                    # of the autograd graph (no grad_placements needed).
                    if info.buffer.requires_grad:
                        raise PipeliningMetadataError(
                            f"Stage {self.stage_index}: recv buffer "
                            f"'{info.input_name}' unexpectedly requires grad "
                            f"before DTensor reconstruction"
                        )
                    mesh = self._mesh_cache.get_mesh(info.tensor_meta.mesh_cache_key)
                    activation = DTensor.from_local(
                        info.buffer,
                        device_mesh=mesh,
                        placements=info.tensor_meta.placements,
                        shape=info.tensor_meta.global_shape,
                        stride=info.tensor_meta.global_stride,
                        run_check=False,
                    ).requires_grad_(effective_requires_grad)
                else:
                    activation = info.buffer.requires_grad_(effective_requires_grad)
                # Activation must be a leaf so backward terminates here.
                if effective_requires_grad and not activation.is_leaf:
                    warnings.warn(
                        f"Stage {self.stage_index}: activation "
                        f"'{info.input_name}' is not a leaf "
                        f"(grad_fn={activation.grad_fn}); using "
                        f"retain_grad() as fallback",
                        stacklevel=2,
                    )
                    activation.retain_grad()
                activations.append(activation)
            else:
                raise PipeliningMetadataError(
                    f"_retrieve_recv_activations expected non-root _RecvInfo but got root arg at index {i}"
                )

        return tuple(activations)