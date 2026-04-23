def test_multi_root_tile_reduce(
        self, tile_size: int, root_ratio: int, dtype: torch.dtype
    ) -> None:
        full_size = 2048
        num_slices_col = 2  # number of tiles on column dimension
        num_slices_row = (
            self.world_size // num_slices_col
        )  # number of tiles on row dimension
        if not (tile_size * num_slices_col <= full_size):
            raise AssertionError(
                f"tile_size * num_slices_col > full_size: "
                f"{tile_size * num_slices_col} vs {full_size}"
            )
        if not (tile_size * num_slices_row <= full_size):
            raise AssertionError(
                f"tile_size * num_slices_row > full_size: "
                f"{tile_size * num_slices_row} vs {full_size}"
            )

        self._init_device()
        group_name = dist.group.WORLD.group_name

        full_inp = symm_mem.empty(
            full_size, full_size, dtype=dtype, device=self.device
        ).fill_(self.rank)
        full_out = symm_mem.empty(
            full_size, full_size, dtype=dtype, device=self.device
        ).fill_(0)

        # Get range of each slice in terms of element indices
        slices_row = [
            slice(s * tile_size, (s + 1) * tile_size) for s in range(num_slices_row)
        ]
        slices_col = [
            slice(s * tile_size, (s + 1) * tile_size) for s in range(num_slices_col)
        ]

        # Active roots, can be a subset of all ranks
        num_active_roots = self.world_size // root_ratio
        active_roots = list(range(num_active_roots))

        # Map rank to slice indices (e.g. rank 0 -> (0, 0), rank 1 -> (0, 1), rank 2 -> (1, 0), rank 3 -> (1, 1))
        map_rank_to_slices = lambda r: (  # noqa: E731
            slices_row[r // num_slices_col],
            slices_col[r % num_slices_col],
        )
        # Populate input tiles
        input_tiles_ij = [map_rank_to_slices(r) for r in active_roots]
        input_tiles = [
            full_inp[slice_i, slice_j] for (slice_i, slice_j) in input_tiles_ij
        ]
        # My output tile (i.e. the one that I will reduce)
        out_tile_ij = map_rank_to_slices(self.rank)
        out_tile = full_out[out_tile_ij[0], out_tile_ij[1]]

        # Reduce the tiles
        torch.ops.symm_mem.multi_root_tile_reduce(
            input_tiles, out_tile, active_roots, group_name
        )

        # Check data
        expected = torch.zeros_like(full_out)
        expected_tile = expected[out_tile_ij[0], out_tile_ij[1]]
        if self.rank in active_roots:
            expected_tile.fill_(self.world_size * (self.world_size - 1) / 2)
        torch.testing.assert_close(full_out, expected)