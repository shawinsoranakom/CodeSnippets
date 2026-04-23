def _setup_world_group_and_device(self):
            default_initialized = is_initialized()
            if not default_initialized:
                init_process_group()

            world_size = get_world_size()
            if self._layout.numel() > world_size:
                raise RuntimeError(
                    f"Mesh should not be bigger than default world size {world_size}, but found {self._layout.numel()} ranks!"
                )

            # Skip device setup for fake backend (cross-compilation mode).
            # The fake backend is used to simulate distributed training on a
            # single process without actual devices, enabling compilation of
            # GPU programs on CPU-only machines.
            backend = get_backend()
            if backend == "fake":
                return _get_default_group()

            # ONLY set the device if the current device is not initialized, if user already
            # set the device before DeviceMesh init, we respect the user's choice.
            device_handle = _get_device_handle(self._device_type)
            if device_handle and not device_handle.is_initialized():
                # auto set the cuda/cuda-like device only if user has not set it, if there's LOCAL_RANK
                # env variable from launchers, we use it to set the device.
                if "LOCAL_RANK" in os.environ:
                    local_rank = int(os.environ["LOCAL_RANK"])
                    logger.info(
                        "Setting default device for the current process based on LOCAL_RANK=%s",
                        local_rank,
                    )
                    device_handle.set_device(local_rank)
                else:
                    # heuristic to set the current cuda/cuda-like device base on num of gpu devices available in each host
                    # NOTE: This device selection would only work for homogeneous hardware.
                    num_devices_per_host = device_handle.device_count()
                    # Skip device setup if no devices are available (cross-compilation mode)
                    if num_devices_per_host == 0:
                        return _get_default_group()
                    warnings.warn(
                        "It seems like you did not set/select the default device for the current process before the DeviceMesh "
                        "initialization or use a launcher (i.e. torchrun) which populates `LOCAL_RANK` environment variable. "
                        "It is recommended to set the current device for the process BEFORE the DeviceMesh initialization so that "
                        "the underlying communicator (i.e. NCCL) can be initialized properly. "
                        "Given that the current process has no default device selected, DeviceMesh will use a heuristic to set the "
                        "device_id via `global_rank % num_devices_per_host`, assuming homogeneous hardware cluster. ",
                        stacklevel=2,
                    )
                    if (
                        world_size > num_devices_per_host
                        and world_size % num_devices_per_host != 0
                    ):
                        raise RuntimeError(
                            f"DeviceMesh only support homogeneous hardware, but found "
                            f"{world_size} ranks and {num_devices_per_host} {self._device_type} devices!"
                        )
                    device_handle.set_device(get_rank() % num_devices_per_host)

            return _get_default_group()