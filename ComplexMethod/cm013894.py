def get_device_properties(device: torch.types.Device = None) -> Any:
            if device is not None:
                if isinstance(device, str):
                    device = torch.device(device)
                    assert device.type == "cuda"
                if isinstance(device, torch.device):
                    device = device.index
            if device is None:
                device = CudaInterface.Worker.current_device()

            if "cuda" not in caching_worker_device_properties:
                device_prop = [
                    torch.cuda.get_device_properties(i)
                    for i in range(torch.cuda.device_count())
                ]
                caching_worker_device_properties["cuda"] = device_prop

            return caching_worker_device_properties["cuda"][device]