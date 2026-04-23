def dtensorify_module(
            module: nn.Module,
            device_mesh,
            *,
            param_placements: list[Placement] | None = None,
            buffer_placements: list[Placement] | None = None,
        ) -> None:
            if param_placements is None:
                param_placements = [Replicate()]
            if buffer_placements is None:
                buffer_placements = [Replicate()]

            for name, p in list(module.named_parameters(recurse=False)):
                if p is None or isinstance(p, DTensor):
                    continue
                dt = DTensor.from_local(p.data, device_mesh, param_placements)
                new_p = nn.Parameter(dt, requires_grad=p.requires_grad)
                setattr(module, name, new_p)

            for name, b in list(module.named_buffers(recurse=False)):
                if b is None or isinstance(b, DTensor):
                    continue
                dt = DTensor.from_local(b, device_mesh, buffer_placements)
                module._buffers[name] = dt

            for child in module.children():
                dtensorify_module(
                    child,
                    device_mesh,
                    param_placements=param_placements,
                    buffer_placements=buffer_placements,
                )