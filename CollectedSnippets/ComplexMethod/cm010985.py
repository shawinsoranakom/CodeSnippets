def determine_local_world_size(nproc_per_node: str):
    try:
        logger.info("Using nproc_per_node=%s.", nproc_per_node)
        return int(nproc_per_node)
    except ValueError as e:
        if nproc_per_node == "cpu":
            num_proc = torch._utils.cpu_count()
            device_type = "cpu"
        elif nproc_per_node == "gpu":
            if not torch.cuda.is_available():
                raise ValueError("Cuda is not available.") from e
            device_type = "gpu"
            num_proc = torch.cuda.device_count()
        elif nproc_per_node == "xpu":
            if not torch.xpu.is_available():
                raise ValueError("Xpu is not available.") from e
            device_type = "xpu"
            num_proc = torch.xpu.device_count()
        elif nproc_per_node == torch._C._get_privateuse1_backend_name():
            if not _get_custom_mod_func("is_available")():
                raise ValueError(f"{nproc_per_node} is not available.") from e
            device_type = nproc_per_node
            num_proc = _get_custom_mod_func("device_count")()
        elif nproc_per_node == "auto":
            if torch.accelerator.is_available():
                num_proc = torch.accelerator.device_count()
                device_type = torch.accelerator.current_accelerator().type  # type: ignore[union-attr]
            else:
                num_proc = torch._utils.cpu_count()
                device_type = "cpu"
        else:
            raise ValueError(
                f"Unsupported nproc_per_node value: {nproc_per_node}"
            ) from e

        logger.info(
            "Using nproc_per_node=%s, setting nproc_per_node to %s since the instance has %s %s",
            nproc_per_node,
            num_proc,
            num_proc,
            device_type,
        )
        return num_proc