def get_group(self, mesh_dim: int | str | None = None) -> ProcessGroup:
            """
            Returns the single ProcessGroup specified by mesh_dim, or, if mesh_dim is not specified and the
            DeviceMesh is 1-dimensional, returns the only ProcessGroup in the mesh.

            Args:
                mesh_dim (str/int, optional): it can be the name of the mesh dimension or the index
                of the mesh dimension. Default is None.

            Returns:
                A :class:`ProcessGroup` object.
            """
            if not hasattr(self, "_dim_group_names"):
                raise RuntimeError("DeviceMesh process groups not initialized!")

            if len(self._layout) > 1 and mesh_dim is None:
                raise RuntimeError(
                    f"Found the DeviceMesh have {len(self._layout)} dimensions",
                    "Optional kwarg `mesh_dim` needs to be specified when device_mesh.ndim > 1.",
                    "If you want to get the list of all the ProcessGroups in the DeviceMesh,"
                    "please use `get_all_groups()` instead.",
                )

            root_mesh = self._get_root_mesh()

            # Quick return if the current device_mesh is a 1D mesh.
            if len(self._layout) == 1 and mesh_dim is None:
                return not_none(_get_pg_from_name(root_mesh, self._dim_group_names[0]))

            root_to_flatten_mapping = root_mesh._flatten_mapping
            if root_to_flatten_mapping and mesh_dim in root_to_flatten_mapping:
                dim_group_name = root_to_flatten_mapping[
                    mesh_dim  # type: ignore[index]
                ]._dim_group_names[0]
                return not_none(_get_pg_from_name(root_mesh, dim_group_name))
            else:
                mesh_dim = (
                    self._get_mesh_dim_by_name(mesh_dim)
                    if isinstance(mesh_dim, str)
                    else mesh_dim
                )
                if not isinstance(mesh_dim, int):
                    raise AssertionError(
                        f"mesh_dim must be an int, got {type(mesh_dim)}"
                    )
                return not_none(
                    _get_pg_from_name(root_mesh, self._dim_group_names[mesh_dim])
                )