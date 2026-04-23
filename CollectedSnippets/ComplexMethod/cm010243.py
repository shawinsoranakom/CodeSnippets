def grid_partitioner(full_grid, grid_blocks, tensor_dims_map):
    if len(full_grid) < 0 or len(full_grid) > 3:
        raise AssertionError(f"full_grid length must be 0-3, got {len(full_grid)}")
    if len(grid_blocks) < 0 or len(grid_blocks) > 3:
        raise AssertionError(f"grid_blocks length must be 0-3, got {len(grid_blocks)}")

    import itertools

    def generate_grid_points():
        for fg, mg in zip(full_grid, grid_blocks, strict=False):
            yield range(0, fg, mg)

    def generate_sliced_tensors(slices):
        for t, t_dims in tensor_dims_map.items():
            yield next(multidim_slicer(t_dims, slices, t))

    for grid_point in itertools.product(*generate_grid_points()):
        grid = [
            min(fg - gp, mg)
            for fg, gp, mg in zip(full_grid, grid_point, grid_blocks, strict=False)
        ]
        slices = [slice(gp, gp + g) for gp, g in zip(grid_point, grid, strict=False)]
        # grid_points are iterated in a "contiguous" order, i.e.
        # left dimensions traversed slower than right dimensions.
        # This order is reversed for CUDA grids.
        yield grid[::-1], *generate_sliced_tensors(slices)