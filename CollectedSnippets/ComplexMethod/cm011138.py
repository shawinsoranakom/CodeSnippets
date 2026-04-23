def _get_grad_inner_tensor(self, grad: torch.Tensor) -> torch.Tensor:
        if self.is_dtensor:
            if isinstance(grad, AsyncCollectiveTensor):
                grad = grad.wait()
            if not isinstance(grad, DTensor):
                raise AssertionError(f"Expected DTensor, got {type(grad)}")
            if self._unsharded_dtensor_spec is None:
                raise AssertionError(
                    "Expected _unsharded_dtensor_spec for DTensor param"
                )
            placements = self._unsharded_dtensor_spec.placements
            if self.mesh_info.is_spmd_mesh:
                # Only redistribute non-DP dims; keep Partial on DP dims
                # so FSDP's reduce-scatter handles them directly, avoiding
                # a redundant all-reduce on the DP dimensions.
                target_placements = tuple(
                    grad.placements[i] if i in self._dp_dim_indices else placements[i]
                    for i in range(len(placements))
                )
                if target_placements != grad.placements:
                    if len(placements) != len(grad.placements):
                        raise AssertionError(
                            f"Expected same placement length: {placements=} {grad.placements=}"
                        )
                    grad = grad.redistribute(placements=target_placements)
            else:
                if placements != grad.placements:
                    if len(placements) != len(grad.placements):
                        raise AssertionError(
                            f"Expected same placement length: {placements=} {grad.placements=}"
                        )
                    grad = grad.redistribute(placements=placements)
            grad = grad._local_tensor
        return grad