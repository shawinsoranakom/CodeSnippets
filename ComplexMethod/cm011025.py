def _unflatten(
            self,
            dim: int | str,
            mesh_sizes: tuple[int, ...],
            mesh_dim_names: tuple[str, ...],
            backend_override: dict[
                str, str | C10dBackend.Options | tuple[str, C10dBackend.Options]
            ]
            | None = None,
        ) -> "DeviceMesh":
            """
            Returns a DeviceMesh by unflatten the current DeviceMesh.

            This api can be used to unflatten a N-D DeviceMesh into N-1+len(mesh_sizes)-D meshes or submeshes.
            The dim is the dimension to be unflattened which can be either a string or an integer.

            The mesh_sizes is a tuple which specifies the shape of the mesh unflatten into for the given dim.
            The mesh_dim_names is a list of strings which specifies the names of the dimensions of the mesh unflatten into.
            Its length must match the length of mesh_sizes.

            For example, if we have a 1D mesh DeviceMesh([0, 1, 2, 3, 4, 5, 6, 7], mesh_dim_names=("world")),
            calling mesh_1d._unflatten(0, (2, 2, 4), ["dp", "pp", "tp"]) will create a 3D mesh
            DeviceMesh([[[0, 1], [2, 3]], [[4, 5], [6, 7]]], mesh_dim_names=("dp", "cp", "tp")).

            Note that after calling the unflatten, there is no access to the unflattened dimension in mesh_1d, one can only
            use the newly unflattened mesh to slice out the unflattened mesh dims.
            """
            if isinstance(dim, int) and dim >= self.ndim:
                raise ValueError(
                    f"dim {dim} specified in `_unflatten` is out of range {self.ndim}"
                )
            elif isinstance(dim, str) and dim not in not_none(self.mesh_dim_names):
                raise ValueError(
                    f"dim {dim} specified in `_unflatten` is not in {self.mesh_dim_names}"
                )

            if len(mesh_sizes) != len(mesh_dim_names):
                raise RuntimeError(
                    "mesh_dim_names must have same length as mesh_sizes in _unflatten!"
                )

            if isinstance(dim, str):
                dim = not_none(self.mesh_dim_names).index(dim)

            if backend_override is not None:
                backend_override_tuple = tuple(
                    _normalize_backend_override(
                        backend_override,  # type: ignore[arg-type]
                        len(mesh_sizes),
                        mesh_dim_names,
                    )
                )
            else:
                backend_override_tuple = ((None, None),) * len(mesh_dim_names)

            return self._create_unflatten_mesh(
                dim,
                mesh_sizes,
                mesh_dim_names,
                backend_override_tuple,
            )