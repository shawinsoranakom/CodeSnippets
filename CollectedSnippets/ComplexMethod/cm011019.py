def __init__(
            self,
            device_type: str,
            mesh: "torch.Tensor | ArrayLike | None" = None,
            *,
            mesh_dim_names: tuple[str, ...] | None = None,
            backend_override: tuple[BackendConfig, ...] | None = None,
            _init_backend: bool = True,
            _rank: int | None = None,
            _layout: _MeshLayout | None = None,
            _rank_map: torch.Tensor | None = None,
            _root_mesh: "DeviceMesh | None" = None,
        ) -> None:
            # no-op in OSS, logs API usage metrics in meta-internal runs
            torch._C._log_api_usage_once(
                "torch.distributed.device_mesh.DeviceMesh.__init__"
            )
            if mesh is not None:
                if _layout is not None or _rank_map is not None:
                    raise TypeError(
                        "Cannot provide _layout and/or _rank_map if passing explicit mesh"
                    )
                if isinstance(mesh, torch.Tensor) and mesh.device.type != "cpu":
                    raise ValueError(f"`mesh` must be a CPU tensor, got {mesh}")
                mesh_tensor = (
                    mesh.detach().to(dtype=torch.int).contiguous()
                    if isinstance(mesh, torch.Tensor)
                    else torch.tensor(mesh, device="cpu", dtype=torch.int)
                )
                _layout = _MeshLayout(mesh_tensor.size(), mesh_tensor.stride())
                _rank_map = mesh_tensor.flatten()
            else:
                if _layout is None or _rank_map is None:
                    raise TypeError(
                        "The mesh argument is required except for PRIVATE USAGE ONLY!"
                    )

            if not _layout.check_non_overlap():
                raise AssertionError(
                    "Please use a non-overlapping layout when creating a DeviceMesh."
                )
            if _rank_map.ndim != 1:
                raise AssertionError("The rank map must be 1-dimensional")
            if not _rank_map.is_contiguous():
                raise AssertionError("The rank map must be contiguous")
            if _rank_map.numel() < _layout.cosize():
                raise AssertionError(
                    f"The rank map contains {_rank_map.numel()} element, "
                    f"which isn't large enough for layout {_layout}"
                )

            self._device_type = device_type
            self._layout = _layout
            self._rank_map = _rank_map
            self._mesh_dim_names = tuple(mesh_dim_names) if mesh_dim_names else None
            self._root_mesh = _root_mesh

            if backend_override is None:
                backend_override = ((None, None),) * len(self._layout)
            elif len(backend_override) != len(self._layout):
                raise ValueError(
                    f"backend_override should have the same length as the number of mesh dimensions, "
                    f"but got {len(backend_override)} and {len(self._layout)}."
                )
            # Internal bookkeeping for the device mesh.
            self._layout = (
                _layout
                if _layout
                else _MeshLayout(self.mesh.size(), self.mesh.stride())
            )
            if not self._layout.check_non_overlap():
                raise AssertionError(
                    "Please use a non-overlapping layout when creating a DeviceMesh."
                )
            # Because we still need to support slicing of flattened dim from root mesh, so we don't check stride here.
            if self._layout.numel() != self.mesh.numel():
                raise AssertionError(
                    "Please use a valid layout when creating a DeviceMesh."
                    f"The layout {self._layout} is not consistent with the mesh size {self.mesh.size()}."
                )

            # private field to pre-generate DeviceMesh's hash
            self._flatten_rank_map = tuple(self._rank_map.tolist())
            self._thread_id = None
            # Initialize instance-specific flatten mapping
            self._flatten_mapping = {}
            # Initialize process group registry
            self._pg_registry = {}

            # Skip process group initialization if xla device or init backend is False
            # TODO(yeounoh) implement DeviceMesh backend and register XLA backend.
            if device_type != "xla":
                # always try to create default (world) pg, even if it is not initialized
                # already. The world pg is used for device mesh identity (rank) on each
                # process (we need to know if the current global rank is in the mesh or not).
                if _init_backend:
                    self._setup_world_group_and_device()
                    self._dim_group_names = self._init_process_groups(
                        self._layout,
                        self._rank_map,
                        self._mesh_dim_names,
                        backend_override,
                    )
                    # Populate the process group registry
                    # If we have a root mesh, add to root's registry for lookups
                    target_registry = (
                        self._root_mesh._pg_registry
                        if self._root_mesh is not None
                        else self._pg_registry
                    )
                    for name in self._dim_group_names:
                        pg = _resolve_process_group(name)
                        if pg is not None:
                            target_registry[name] = pg

                if is_initialized() and get_backend() == "threaded":
                    self._thread_id = threading.get_ident()

                # Now that the process group is initialized, we can get the rank
                if _rank is None:
                    self._rank = get_rank()
                else:
                    self._rank = _rank

                self._coordinate_on_dim = self._compute_coordinate_on_dim()

            self._hash: int | None = None