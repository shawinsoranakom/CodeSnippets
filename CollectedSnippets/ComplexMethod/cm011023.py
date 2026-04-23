def _get_slice_mesh_layout(
            self, mesh_dim_names: tuple[str, ...]
        ) -> _MeshLayout:
            """
            Validate whether the mesh_dim_names is valid for slicing the given device_mesh.
            If valid, return dim indexes of the slice mesh in the device mesh.
            """
            slice_from_root = True
            if self != self._get_root_mesh():
                slice_from_root = False

            # The slice mesh_dim_names should consist either the current device_mesh's mesh_dim_names
            # or its flattened mesh's mesh_dim_names if it's root_mesh.
            flatten_name_to_root_layout = (
                {
                    key: mesh._layout
                    for key, mesh in self._get_root_mesh()._flatten_mapping.items()
                }
                if slice_from_root
                else {}
            )
            valid_mesh_dim_names = [
                *not_none(self._mesh_dim_names),
                *flatten_name_to_root_layout,
            ]

            if not all(
                mesh_dim_name in valid_mesh_dim_names
                for mesh_dim_name in mesh_dim_names
            ):
                raise KeyError(
                    f"Invalid mesh_dim_names {mesh_dim_names} specified. "
                    f"Valid mesh_dim_names are {valid_mesh_dim_names}."
                )

            layout_sliced = []
            for name in mesh_dim_names:
                if name in not_none(self._mesh_dim_names):
                    layout_sliced.append(
                        self._layout[not_none(self._mesh_dim_names).index(name)]
                    )
                elif name in flatten_name_to_root_layout:
                    warnings.warn(
                        "Slicing a flattened dim from root mesh will be deprecated in PT 2.11. "
                        "Users need to bookkeep the flattened mesh directly. ",
                        stacklevel=2,
                    )
                    layout_sliced.append(flatten_name_to_root_layout[name])

            sliced_sizes = tuple(l.sizes for l in layout_sliced)
            sliced_strides = tuple(l.strides for l in layout_sliced)

            # The check below is from DeviceMesh's implementation before adopting CuTe layout for internal
            # bookkeeping and it can be removed but we need to define what is the expected behavior.
            # TODO: Remove the below check and define the expected behavior.
            # Validate the order of the slice mesh dim indices.
            # This needs to be in ascending order.
            pre_stride = -1
            for stride in reversed(sliced_strides):
                # Note that with CuTe layout, we can support slicing flattened non-contiguous mesh dims with no problem.
                # But we don't see a use case for now so we don't want to support it.
                if not is_int(stride):
                    raise NotImplementedError(
                        "Currently, this only allows slicing out a contiguous flattened dim."
                    )
                # Note that with CuTe layout, we can support slicing non-ascending order dims with no problem.
                # But we don't see a use case for now so we don't want to support it.
                if stride < pre_stride:
                    raise KeyError(
                        f"Invalid mesh_dim_names {mesh_dim_names} specified. "
                        "Mesh dim indices should be in ascending order."
                    )
                pre_stride = stride

            # When users sliced dim_names outside from current mesh, we will check whether
            # there is layout overlap.
            # TODO: Eventually we will just directly throw error here because
            # we will deprecate the slicing of flattened dim_name from root mesh.
            layout_sliced = _MeshLayout(sliced_sizes, sliced_strides)
            if not layout_sliced.check_non_overlap():
                raise RuntimeError(
                    f"Slicing overlapping dim_names {mesh_dim_names} is not allowed."
                )

            return layout_sliced