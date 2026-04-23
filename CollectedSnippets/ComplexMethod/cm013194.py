def _ensure_processes_spawned(cls):
        """
        Lazily spawn worker processes on first test run.
        This supports instantiate_device_type_tests which calls setUpClass during
        class creation (before any tests run), when spawning would be premature.
        """
        if cls._processes_spawned:
            return

        # Handle method, property, and string attribute for device_type
        # (instantiate_device_type_tests sets device_type as a string attribute,
        # making this compatible as a drop-in replacement for MultiProcessTestCase)
        device_type_attr = cls.__dict__.get("device_type", cls.device_type)
        if isinstance(device_type_attr, classmethod):
            device_type = device_type_attr.__func__(cls)
        elif isinstance(device_type_attr, property):
            # Note: fget expects an instance but we pass cls since no instance
            # exists yet. This works because DTensorTestMixin.device_type only
            # accesses class-level attributes (world_size, module constants).
            device_type = device_type_attr.fget(cls)
        elif callable(device_type_attr):
            device_type = device_type_attr()
        else:
            device_type = device_type_attr

        # Get world_size (handles both class variable and property)
        cls.world_size = cls._get_world_size(device_type)

        # Check if the specified backend is available before spawning processes
        backend = cls.backend_str() if callable(cls.backend_str) else cls.backend_str
        if backend is not None:
            backend_checks = {
                "nccl": c10d.is_nccl_available,
                "gloo": c10d.is_gloo_available,
                "mpi": c10d.is_mpi_available,
                "xccl": c10d.is_xccl_available,
            }
            check_fn = backend_checks.get(backend)
            if check_fn is not None and not check_fn():
                raise unittest.SkipTest(f"Backend '{backend}' is not available")

        logger.info(
            f"Testing class {cls.__name__} on {cls.world_size} {device_type}"  # noqa: G004
        )

        cls._spawn_processes(cls.world_size)
        cls._processes_spawned = True