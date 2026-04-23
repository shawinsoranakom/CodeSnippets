def constant_name(self, name: str, device_override: torch.device | None) -> str:
        """
        We AOT copy constants to the devices they are needed on.
        If device_override doesn't match the constant's device, then
        copy it and return a different name.
        """
        if self.constants[name].device == device_override or device_override is None:
            return name
        with torch.utils._python_dispatch._disable_current_modes():
            # caller might have OrderedSet fake tensor mode which will create a fake tensor
            # when calling .to, so unset modes here
            non_dup_const_name = self.allocate_non_dup_const_name(
                f"{name}_{device_override.type}{device_override.index or 0}",
                self.constants[name].to(device_override),
            )

            assert non_dup_const_name in self.constants, (
                f"{non_dup_const_name} should be in V.graph.constants already"
            )

            # register device-copied buffers and parameters to graph as well
            # to codegen correct torch::aot_inductor::ConstantType for them rather than `Unknown`
            if any(
                name == normalize_name(buffer_name)
                for buffer_name in self.named_buffers
            ):
                self.named_buffers[non_dup_const_name] = self.constants[
                    non_dup_const_name
                ]

            if any(
                name == normalize_name(param_name)
                for param_name in self.named_parameters
            ):
                self.named_parameters[non_dup_const_name] = self.constants[
                    non_dup_const_name
                ]

            return non_dup_const_name