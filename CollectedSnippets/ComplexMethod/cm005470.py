def initialize_tensor_parallelism(
    tp_plan: str | dict[str, str] | None, tp_size: int | None = None, device_mesh=None, device_map=None
):
    r"""
    Sets up the device mesh and initialized the backend for tensor parallelism.
    This function is called when the model is loaded and the TP plan is set to 'auto'.
    """
    if tp_size is not None and tp_plan is None:
        raise ValueError("tp_plan has to be set when tp_size is passed.")
    if tp_plan is not None and device_map is not None:
        raise ValueError("`tp_plan` and `device_map` are mutually exclusive. Choose either one for parallelization.")
    if device_mesh is None:
        if not is_torch_greater_or_equal("2.5"):
            raise OSError("Tensor parallel is only supported for `torch>=2.5`.")

        # Detect the accelerator on the machine. If no accelerator is available, it returns CPU.
        device_type = torch._C._get_accelerator().type
        if device_type == "mps":
            raise RuntimeError("Tensor parallelism is not supported on MPS devices.")
        current_device = getattr(torch, device_type)
        if not torch.distributed.is_initialized():
            try:
                rank = int(os.environ["RANK"])
                local_rank = int(os.environ["LOCAL_RANK"])
                world_size = int(os.environ["WORLD_SIZE"])

                backend_map = {"cuda": "nccl", "cpu": "gloo", "xpu": "xccl", "hpu": "hccl", "neuron": "neuron"}
                backend = backend_map.get(device_type)

                torch.distributed.init_process_group(backend=backend, rank=rank, world_size=world_size)
                current_device = getattr(torch, device_type)
                if device_type != "cpu":
                    current_device.set_device(local_rank)

            except Exception as e:
                raise OSError(
                    "We tried to initialize torch.distributed for you, but it failed. Make "
                    "sure you init torch distributed in your script to use `tp_plan`."
                ) from e

        if device_type != "cpu":
            current_device.set_device(int(os.environ["LOCAL_RANK"]))
            index = current_device.current_device()
            tp_device = torch.device(device_type, index)
            device_map = tp_device
        else:
            tp_device = torch.device(device_type)
            device_map = device_type or {}

        tp_size = tp_size if tp_size is not None else torch.distributed.get_world_size()
        device_mesh = torch.distributed.init_device_mesh(tp_device.type, (tp_size,))
    else:
        if device_mesh.ndim > 1:
            if "tp" not in device_mesh.mesh_dim_names:
                raise ValueError(
                    "When using `tp_plan` and n-d `device_mesh`, it must contain a 'tp' dimension. "
                    "Please provide a valid `device_mesh`."
                )
            device_mesh = device_mesh["tp"]
        tp_size = device_mesh.size()
        device_map = torch.device(f"{device_mesh.device_type}:{int(os.environ['LOCAL_RANK'])}")

    return device_map, device_mesh, tp_size