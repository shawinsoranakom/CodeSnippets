def register_backend(
        cls,
        name,
        func,
        extended_api: bool = False,
        devices: str | list[str] | None = None,
    ) -> None:
        """
        Register a new backend with the given name and instantiating function.

        This class method is used by 3rd party ``ProcessGroup`` extension to
        register new backends.

        Args:
            name (str): Backend name of the ``ProcessGroup`` extension. It
                        should match the one in ``init_process_group()``.
            func (function): Function handler that instantiates the backend.
                             The function should be implemented in the backend
                             extension and takes four arguments, including
                             ``store``, ``rank``, ``world_size``, and ``timeout``.
            extended_api (bool, optional): Whether the backend supports extended argument structure.
                                           Default: ``False``. If set to ``True``, the backend
                                           will get an instance of ``c10d::DistributedBackendOptions``, and
                                           a process group options object as defined by the backend implementation.
            device (str or list of str, optional): device type this backend
                            supports, e.g. "cpu", "cuda", etc. If `None`,
                            assuming both "cpu" and "cuda"

        .. note:: This support of 3rd party backend is experimental and subject to change.

        """
        # This takes care of CUSTOM Out-of-tree backend types, update in backend_list indicates availability
        if not hasattr(Backend, name.upper()):
            setattr(Backend, name.upper(), name.lower())
        if name.lower() not in Backend.backend_list:
            Backend.backend_list.append(name.lower())

        if devices is not None:
            for device in devices:
                current = Backend.default_device_backend_map.get(device)
                # Allow remapping from fake backend to actual backend (e.g., HPU from fake to HCCL)
                # but prevent fake backend from claiming devices
                if current is None or (current == "fake" and name.lower() != "fake"):
                    Backend.default_device_backend_map[device] = name.lower()

        Backend.backend_type_map[name.lower()] = ProcessGroup.BackendType.CUSTOM

        # Update device capability matrix in Backend class
        if devices is None:
            # This is more of a backward support for groups like `threaded`:
            # assume default devices "cpu" and "cuda", but warn
            warnings.warn(
                f"Device capability of {name} unspecified, assuming `cpu` and "
                "`cuda` or `xpu`. Please specify it via the `devices` argument of "
                "`register_backend`.",
                stacklevel=2,
            )
            Backend.backend_capability[name.lower()] = (
                ["cpu", "cuda", "xpu"] if torch.xpu.is_available() else ["cpu", "cuda"]
            )
        elif isinstance(devices, str):
            # Single device string specified. Simply convert to list.
            Backend.backend_capability[name.lower()] = [devices]
        else:
            Backend.backend_capability[name.lower()] = devices

        Backend._plugins[name.upper()] = Backend._BackendPlugin(func, extended_api)