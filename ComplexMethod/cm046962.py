def _assign(module, prefix):
        params = list(module.named_parameters(remove_duplicate = False))
        if not params:
            bufs = list(module.named_buffers())
            if bufs:
                device_map[prefix] = bufs[0][1].device
            return
        devices = {p.device for _, p in params}
        if len(devices) == 1:
            device_map[prefix] = next(iter(devices))
        else:
            for child_name, child in module.named_children():
                child_prefix = f"{prefix}.{child_name}" if prefix else child_name
                _assign(child, child_prefix)
            for pname, param in module.named_parameters(remove_duplicate = False):
                if "." not in pname:
                    full = f"{prefix}.{pname}" if prefix else pname
                    if not any(
                        full == k or full.startswith(k + ".") for k in device_map
                    ):
                        device_map[full] = param.device