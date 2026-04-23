def _retrieve_recv_grads(
        self,
        bwd_chunk_id: int,
    ):
        """
        Retrieve the gradients received for the current stage during backward.

        Handles None gradients gracefully (for inputs that don't require grad).
        """
        recv_infos = self.grad_recv_info[bwd_chunk_id]

        grads: list[torch.Tensor | None] = []
        for i, info in enumerate(recv_infos):
            if not isinstance(info, _RecvInfo):
                raise PipeliningMetadataError(
                    f"Expected _RecvInfo but got {type(info)}"
                )
            if not info.is_root_arg:
                # Gradients can be None for non-differentiable outputs
                if info.buffer is None:
                    if info.tensor_meta is not None:
                        raise PipeliningMetadataError(
                            f"Grad recv '{info.input_name}': buffer is None but tensor_meta is not None"
                        )
                    grads.append(None)
                    continue
                if info.tensor_meta is None:
                    raise PipeliningMetadataError(
                        f"Grad recv '{info.input_name}': buffer is not None but tensor_meta is None"
                    )
                if isinstance(info.tensor_meta, _DTensorMeta):
                    # Reconstruct DTensor gradient from local tensor + metadata
                    mesh = self._mesh_cache.get_mesh(info.tensor_meta.mesh_cache_key)
                    grad = DTensor.from_local(
                        info.buffer,
                        device_mesh=mesh,
                        placements=info.tensor_meta.placements,
                        shape=info.tensor_meta.global_shape,
                        stride=info.tensor_meta.global_stride,
                        run_check=False,
                    )
                else:
                    grad = info.buffer
                grads.append(grad)
            else:
                raise PipeliningMetadataError(
                    f"grad_recv_info should not contain root args, but found one at index {i}"
                )

        return tuple(grads)