def get_device_properties(device: torch.types.Device = None) -> Any:
            if device is not None:
                if isinstance(device, str):
                    device = torch.device(device)
                    assert device.type == "mtia"
                if isinstance(device, torch.device):
                    device = device.index
            if device is None:
                device = MtiaInterface.Worker.current_device()

            if "mtia" not in caching_worker_device_properties:
                device_prop = [
                    torch.mtia.get_device_properties(i)
                    for i in range(torch.mtia.device_count())
                ]
                caching_worker_device_properties["mtia"] = device_prop

            return caching_worker_device_properties["mtia"][device]