def do_bench(
        self,
        fn,
        *input_tensors: torch.Tensor,
        out: torch.Tensor | None = None,
    ) -> float:
        device_idx_set = OrderedSet(
            tensor.device.index
            for tensor in [*input_tensors, out]
            if isinstance(tensor, torch.Tensor)
            and is_gpu(tensor.device.type)
            and tensor.device.index is not None
        )
        assert len(device_idx_set) <= 1, f"Can not mix devices {device_idx_set}"
        device_type = next(
            (
                tensor.device.type
                for tensor in input_tensors
                if is_gpu(tensor.device.type)
            ),
            "cuda",
        )
        device_interface = get_interface_for_device(device_type)
        if len(device_idx_set) == 1:
            device_idx = next(iter(device_idx_set))
        else:
            device_idx = device_interface.current_device()
        with device_interface.device(device_idx):  # type: ignore[attr-defined]
            res = benchmarker.benchmark(fn, device=device_type)
            device_interface.synchronize()  # shake out any CUDA errors

        return res