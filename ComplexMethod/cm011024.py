def from_group(
            group: ProcessGroup | list[ProcessGroup],
            device_type: str,
            mesh: "torch.Tensor | ArrayLike | None" = None,
            *,
            mesh_dim_names: tuple[str, ...] | None = None,
        ) -> "DeviceMesh":
            """
            Constructs a :class:`DeviceMesh` with ``device_type`` from an
            existing :class:`ProcessGroup` or a list of existing :class:`ProcessGroup`.

            The constructed device mesh has number of dimensions equal to the
            number of groups passed. For example, if a single process group is passed in,
            the resulted DeviceMesh is a 1D mesh. If a list of 2 process groups is passed in,
            the resulted DeviceMesh is a 2D mesh.

            If more than one group is passed, then the ``mesh`` and ``mesh_dim_names`` arguments
            are required. The order of the process groups passed in determines the topology of
            the mesh. For example, the first process group will be the 0th dimension of the DeviceMesh.
            The `mesh` tensor passed in must have the same number of dimensions as the number of process
            groups passed in, and the order of the dimensions in the `mesh` tensor must match the order
            in the process groups passed in.

            Args:
                group (ProcessGroup or list[ProcessGroup]): the existing ProcessGroup
                    or a list of existing ProcessGroups.
                device_type (str): The device type of the mesh. Currently supports: "cpu",
                    "cuda/cuda-like". Passing in a device type with a GPU index, such as "cuda:0",
                    is not allowed.
                mesh (torch.Tensor or ArrayLike, optional): A multi-dimensional array or an
                    integer tensor describing the layout of devices, where the IDs are global IDs
                    of the default process group. Default is None.
                mesh_dim_names (tuple[str, ...], optional): A tuple of mesh dimension names to assign
                    to each dimension of the multi-dimensional array describing the layout of devices.
                    Its length must match the length of `mesh_shape`. Each string in `mesh_dim_names`
                    must be unique. Default is None.

            Returns:
                DeviceMesh: A :class:`DeviceMesh` object representing the device layout.
            """

            # 1D scenario
            if isinstance(group, ProcessGroup):
                group_ranks = get_process_group_ranks(group)
                if (
                    isinstance(mesh, torch.Tensor) and mesh.tolist() != group_ranks
                ) or (
                    mesh is not None
                    and not isinstance(mesh, torch.Tensor)
                    and mesh != group_ranks
                ):
                    raise ValueError(
                        f"Invalid mesh {str(mesh)} for ProcessGroup with ranks {group_ranks}"
                    )
                mesh = torch.tensor(group_ranks, device="cpu", dtype=torch.int)
                device_mesh = DeviceMesh(
                    device_type,
                    mesh,
                    mesh_dim_names=mesh_dim_names,
                    _init_backend=False,
                )
                device_mesh._dim_group_names = [group.group_name]
                device_mesh._pg_registry[group.group_name] = group
                return device_mesh

            # nD scenario
            groups = list(group)
            if len(groups) == 0:
                raise ValueError("Expects at least one ProcessGroup to be passed")
            if mesh is None:
                raise ValueError("Must pass mesh if passing multiple ProcessGroups")
            if mesh_dim_names is None:
                raise ValueError(
                    "Must pass mesh_dim_names if passing multiple ProcessGroups"
                )
            # When init a DeviceMesh with multiple ProcessGroups directly, we need to make sure
            # the mesh tensor is contiguous. Otherwise, the layout we inferred from the mesh tensor
            # will have larger span than the actual tensor. This is just internal implementation detail
            # and does not affect user facing behavior.
            mesh = (
                mesh.detach().to(dtype=torch.int, device="cpu")
                if isinstance(mesh, torch.Tensor)
                else torch.tensor(mesh, device="cpu", dtype=torch.int)
            )
            if mesh.ndim != len(groups):
                raise ValueError(
                    "Expects mesh with ndim equal to number of ProcessGroups but got "
                    f"mesh {mesh.tolist()} and {len(groups)} ProcessGroups"
                )
            device_mesh = DeviceMesh(
                device_type, mesh, mesh_dim_names=mesh_dim_names, _init_backend=False
            )
            device_mesh._dim_group_names = [group.group_name for group in groups]
            for group in groups:
                device_mesh._pg_registry[group.group_name] = group
            return device_mesh