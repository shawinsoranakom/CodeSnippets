def format_shard_order_str(
        placements: tuple[Placement, ...],
        shard_order: ShardOrder | None = None,
    ) -> str:
        """
        Format DTensor sharding information as a human-readable string.

        This method formats the sharding pattern in mesh-centric order, showing the placement
        for each mesh dimension sequentially. When a tensor dimension is sharded across multiple
        mesh dimensions, the order index indicates the execution sequence of the sharding operations.

        Args:
            placements: Tuple of placement objects for each mesh dimension.
            shard_order: Optional ShardOrder specifying the sharding order.

        Returns:
            String representation of the sharding pattern in mesh-centric format.

        Example:
            For a 3D tensor on a 2x2x2x2 mesh (16 devices) with::

                placements = [Partial(), Shard(1), Shard(1), Replicate()]
                shard_order = (ShardOrderEntry(tensor_dim=1, mesh_dims=(2, 1)),)

            Mesh configuration:
                - mesh_dim_0: Partial reduction (sum)
                - mesh_dim_1: Shard tensor dimension 1 (executed second, order index 1)
                - mesh_dim_2: Shard tensor dimension 1 (executed first, order index 0)
                - mesh_dim_3: Replicate

            Output: ``"PS(1)[1]S(1)[0]R"``

            Explanation:
                - ``P``: mesh dimension 0 has partial reduction
                - ``S(1)[1]``: mesh dimension 1 shards tensor dimension 1 (order index 1 means second)
                - ``S(1)[0]``: mesh dimension 2 shards tensor dimension 1 (order index 0 means first)
                - ``R``: mesh dimension 3 replicates

            The format follows mesh dimension order (0, 1, 2, 3), and when a tensor dimension
            is sharded across multiple mesh dimensions, the bracketed index shows the execution
            order: ``[0]`` is executed first, ``[1]`` is executed second, etc.
        """
        out_str = ""
        # native dtensor-style sharding representation: map from mesh
        # dim to tensor dim
        for mesh_dim, placement in enumerate(placements):
            if _is_shard_like(placement):
                if shard_order is not None:
                    for entry in shard_order:
                        tensor_dim = entry.tensor_dim
                        mesh_dims = entry.mesh_dims

                        if placement.dim == tensor_dim:
                            if mesh_dim not in mesh_dims:
                                raise AssertionError
                            if len(mesh_dims) > 1:
                                out_str += f"{placement}[{mesh_dims.index(mesh_dim)}]"
                            else:
                                # no need to show device order if the tensor dim is
                                # only sharded in one mesh dim
                                out_str += str(placement)
                            break
                else:
                    out_str += str(placement)
            else:
                out_str += str(placement)
        return out_str