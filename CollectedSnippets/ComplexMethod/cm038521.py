def reduce_scatterv(
        self, input_: torch.Tensor, dim: int = -1, sizes: list[int] | None = None
    ):
        world_size = self.world_size

        if dim < 0:
            # Convert negative dim to positive.
            dim += input_.dim()

        # Note: This will produce an incorrect answer if we don't make
        # the input_tensor contiguous. Possible bug in reduce_scatter_tensor?
        input_tensor = input_.movedim(0, dim).contiguous()

        if sizes is not None:
            assert len(sizes) == world_size
            assert input_tensor.shape[0] == sum(sizes)
            chunk_size = sizes[self.rank_in_group]
        else:
            assert input_tensor.shape[0] % world_size == 0
            chunk_size = input_tensor.shape[0] // world_size
        output_shape = (chunk_size,) + input_tensor.shape[1:]

        output = torch.empty(
            output_shape, dtype=input_tensor.dtype, device=input_tensor.device
        )
        if sizes is not None and sizes.count(sizes[0]) != len(sizes):
            # if inputs shape in different ranks is not the same using reduce_scatter
            input_splits = list(input_tensor.split(sizes, dim=0))
            dist.reduce_scatter(output, input_splits, group=self.device_group)
        else:
            dist.reduce_scatter_tensor(output, input_tensor, group=self.device_group)
        # Reshape before returning
        return output.movedim(0, dim).contiguous()