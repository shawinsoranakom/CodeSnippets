def _output_padding(
        self,
        input: Tensor,
        output_size: list[int] | None,
        stride: list[int],
        padding: list[int],
        kernel_size: list[int],
        num_spatial_dims: int,
        dilation: list[int] | None = None,
    ) -> list[int]:
        if output_size is None:
            ret = _single(self.output_padding)  # converting to list if was not already
        else:
            has_batch_dim = input.dim() == num_spatial_dims + 2
            num_non_spatial_dims = 2 if has_batch_dim else 1
            if len(output_size) == num_non_spatial_dims + num_spatial_dims:
                output_size = output_size[num_non_spatial_dims:]
            if len(output_size) != num_spatial_dims:
                raise ValueError(
                    f"ConvTranspose{num_spatial_dims}D: for {input.dim()}D input, output_size must have {num_spatial_dims} "
                    f"or {num_non_spatial_dims + num_spatial_dims} elements (got {len(output_size)})"
                )

            min_sizes = torch.jit.annotate(list[int], [])
            max_sizes = torch.jit.annotate(list[int], [])
            for d in range(num_spatial_dims):
                dim_size = (
                    (input.size(d + num_non_spatial_dims) - 1) * stride[d]
                    - 2 * padding[d]
                    + (dilation[d] if dilation is not None else 1)
                    * (kernel_size[d] - 1)
                    + 1
                )
                min_sizes.append(dim_size)
                max_sizes.append(min_sizes[d] + stride[d] - 1)

            for i in range(len(output_size)):
                size = output_size[i]
                min_size = min_sizes[i]
                max_size = max_sizes[i]
                if size < min_size or size > max_size:
                    raise ValueError(
                        f"requested an output size of {output_size}, but valid sizes range "
                        f"from {min_sizes} to {max_sizes} (for an input of {input.size()[2:]})"
                    )

            res = torch.jit.annotate(list[int], [])
            for d in range(num_spatial_dims):
                res.append(output_size[d] - min_sizes[d])

            ret = res
        return ret