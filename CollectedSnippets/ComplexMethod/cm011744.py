def create_backend(self, device: torch.device) -> BaseScheduling:
        assert not is_gpu(device.type) or device.index is not None, (
            f"{device} should have been normalized in lowering"
        )
        V.graph.add_device_info(device)

        device_scheduling = get_scheduling_for_device(device.type)
        if device_scheduling is None:
            raise RuntimeError(f"Unsupported device type: {device.type}")

        if not has_triton():
            if (
                device.type == "cuda"
                and (device_props := torch.cuda.get_device_properties(device)).major < 7
            ):
                raise GPUTooOldForTriton(device_props, inspect.currentframe())
            elif is_gpu(device.type) and not device.type == "mps":
                raise TritonMissing(inspect.currentframe())

        return device_scheduling(self)