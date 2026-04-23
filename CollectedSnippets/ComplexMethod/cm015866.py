def forward(self, x, y):
                output = torch.zeros_like(x)
                if autotune and num_dims == 2:
                    x_elements = output.size()[0]
                    y_elements = output.size()[1]
                else:
                    n_elements = output.numel()

                # Select grid
                if autotune and num_dims == 2:
                    if grid_type == 1:
                        grid = (x_elements, y_elements)
                    elif grid_type == 2:
                        grid = lambda meta: (  # noqa: E731
                            triton.cdiv(x_elements, meta["BLOCK_SIZE_X"]),
                            triton.cdiv(y_elements, meta["BLOCK_SIZE_Y"]),
                        )
                    else:

                        def grid_fn(meta):
                            return (
                                triton.cdiv(x_elements, meta["BLOCK_SIZE_X"]),
                                triton.cdiv(y_elements, meta["BLOCK_SIZE_Y"]),
                            )

                        grid = grid_fn
                else:
                    if grid_type == 1:
                        grid = (n_elements,)
                    elif grid_type == 2:
                        grid = lambda meta: (  # noqa: E731
                            triton.cdiv(n_elements, meta["BLOCK_SIZE"]),
                        )
                    else:

                        def grid_fn(meta):
                            return (triton.cdiv(n_elements, meta["BLOCK_SIZE"]),)

                        grid = grid_fn

                # Select kernel
                if autotune:
                    if num_dims == 1:
                        add_kernel_autotuned[grid](x, y, output, n_elements)
                    else:
                        add_kernel_2d_autotuned[grid](
                            x, y, output, x_elements, y_elements
                        )
                else:
                    add_kernel[grid](x, y, output, n_elements, BLOCK_SIZE=16)
                return output