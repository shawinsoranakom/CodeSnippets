def merge_devices(t: object) -> None:
            nonlocal common_device
            nonlocal is_cpu_zero_dim
            if not isinstance(t, FakeTensor):
                return

            if common_device is None:
                common_device = t.device
                is_cpu_zero_dim = cpu_zero_dim(t)
                return

            t_is_cpu_zero_dim = cpu_zero_dim(t)
            if t.device == common_device:
                if is_cpu_zero_dim:
                    is_cpu_zero_dim = t_is_cpu_zero_dim
                return

            is_bypass_zero_dim_cpu_tensor_check_op = (
                func in bypass_zero_dim_cpu_tensor_check_ops
            )

            # mismatching devices !
            # if current tensor is cpu 0 dim, defer to existing device
            if t_is_cpu_zero_dim and not is_bypass_zero_dim_cpu_tensor_check_op:
                return

            # current device is from cpu 0 dim tensor, overwrite
            if is_cpu_zero_dim and not is_bypass_zero_dim_cpu_tensor_check_op:
                common_device = t.device
                is_cpu_zero_dim = t_is_cpu_zero_dim
                return

            # if still device mismatches we will check ops which can work
            # on different devices for ex. _foreach_copy, and one of the
            # device must be cpu in this case we will return from here without
            # throwing an error
            if func in mixed_device_fns:
                if any(map(is_device_cpu, (common_device, t.device))):
                    return

            if func in meta_rhs_mixed_device_fns:
                if any(map(is_device_meta, (common_device, t.device))):
                    return

            # if prefer_device_type is set, prefer that device type over others
            prefer_device_type = torch._functorch.config.fake_tensor_prefer_device_type
            if prefer_device_type is not None:
                common_has_preferred = prefer_device_type in common_device.type
                t_has_preferred = prefer_device_type in t.device.type

                if not common_has_preferred and t_has_preferred:
                    # Switch to the preferred device type
                    common_device = t.device
                    is_cpu_zero_dim = t_is_cpu_zero_dim
                    return
                elif common_has_preferred and not t_has_preferred:
                    # Keep the existing preferred device type
                    return

            # mismatching devices of non-zero dim tensors, throw
            # This might be valid behavior and need to be explicitly modeled, e.g. reshape_as
            raise RuntimeError(
                f"Unhandled FakeTensor Device Propagation for {func}, found two different devices {common_device}, {t.device}"
            )