def to_dist_tensor(
        self, t: torch.Tensor, mesh: DeviceMesh, placements: list[Placement]
    ) -> torch.Tensor:
        if type(t) is torch.Tensor or type(t) is nn.Parameter or type(t) is LocalTensor:
            if self.is_supported_tensor(t):
                self.hit += 1
                if t.ndim == 0:
                    # scalar tensor by default will be replicated
                    r = distribute_tensor(t, mesh, [Replicate()] * mesh.ndim)
                else:
                    # distribute non-scalar tensors
                    r = distribute_tensor(t, mesh, placements)
                if isinstance(t, nn.Parameter):
                    r = nn.Parameter(  # type: ignore[assignment]
                        r, requires_grad=r.requires_grad
                    )
                return r
            else:
                self.miss += 1
                return t
        elif torch.overrides.is_tensor_like(t):
            # Blindly converting tensor subclasses to dist tensor can cause
            # unpredictable problems, we explicitly disable this conversion
            # for now (i.e. we don't support DTensor holding tensor subclass
            # until there's a strong reason later).
            self.miss += 1
            return t
        else:
            raise RuntimeError(f"Trying to convert to DTensor, but got {type(t)}")