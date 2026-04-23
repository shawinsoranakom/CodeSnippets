def get_coordinate(self: DeviceMesh) -> list[SymInt] | None:
        # NB: In order to support submeshes the code below recreates for each
        # rank submesh with the same mesh dimensions as current mesh. We are
        # doing this because when submesh is created it is created for a particular
        # rank (therefore below we are patching get_rank method). We are trying to
        # limit the invasiveness of local tensor.
        lm = enabled_local_tensor_mode()
        if lm is None:
            raise AssertionError("Unexpectedly not in LocalTensorMode")

        # Check cache first (fast path without lock)
        mesh_id = id(self)
        if mesh_id in lm._coordinate_cache:
            return lm._coordinate_cache[mesh_id]

        # Acquire lock for thread safety in MPMD contexts
        with lm._coordinate_cache_lock:
            # Double-check after acquiring lock
            if mesh_id in lm._coordinate_cache:
                return lm._coordinate_cache[mesh_id]

            coords: list[dict[int, int]] = [{} for _ in range(self.ndim)]
            # Clone rank_map to avoid "Cannot set version_counter for inference tensor"
            # error when running under torch.inference_mode()
            rank_map = self._rank_map.clone()
            for r in lm.ranks:
                rank_tensor = self._layout.remap_to_tensor(rank_map)
                rank_coords = (rank_tensor == r).nonzero().tolist()
                if len(rank_coords) != 1:
                    raise AssertionError
                for d, c in enumerate(rank_coords[0][1:]):
                    coords[d][r] = c

            out = [torch.SymInt(LocalIntNode(c)) for c in coords]
            # Cache the result
            lm._coordinate_cache[mesh_id] = out
            # The output contains coordinates for each of the ranks with respect to
            # their meshes formed from root mesh and selecting the same dimensions
            # as the current mesh.
            return out