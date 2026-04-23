def find_device(
        tensor_args: Sequence[torch.Tensor] | None, example_output: Sequence[Any]
    ) -> Any:
        non_torch_bind_tensor_args = (
            [t for t in tensor_args if not isinstance(t, TorchBindObject)]
            if tensor_args
            else None
        )
        if non_torch_bind_tensor_args:
            assert tensor_args
            devices = [arg.get_device() for arg in tensor_args if arg.get_device()]
            return devices[0]
        if isinstance(example_output, torch.Tensor):
            return example_output.device
        if isinstance(
            example_output, (torch._C.ScriptObject, FakeScriptObject)
        ) or is_opaque_value(example_output):
            return torch.device("cpu")
        if isinstance(example_output, (list, tuple)):
            device_set = OrderedSet(
                # pyrefly: ignore [bad-argument-type]
                FallbackKernel.find_device(None, x)
                for x in example_output
            )
            # Remove None
            devices = [device for device in device_set if device]
            if len(devices) == 1:
                return devices[0]
            if not devices:
                return None
            for device in devices:
                assert isinstance(device, torch.device)
                if is_gpu(device.type):
                    return device
            return devices[0]
        return None