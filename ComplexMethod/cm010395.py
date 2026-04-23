def triton_kernel_wrapper_mutation_dense(
    *,
    kernel_idx: int,
    constant_args_idx: int,
    grid: list["TritonGridType"],
    tma_descriptor_metadata: TMADescriptorMetadata,
    kwargs: dict[str, Any],
) -> None:
    from torch._inductor.codegen.wrapper import user_defined_kernel_grid_fn_code

    kernel = kernel_side_table.get_kernel(kernel_idx)
    constant_args = kernel_side_table.get_constant_args(constant_args_idx)

    if len(grid) == 1:
        grid_fn = grid[0]
    else:
        fn_name, code = user_defined_kernel_grid_fn_code(
            # pyrefly: ignore [missing-attribute]
            kernel.fn.__name__,
            # pyrefly: ignore [missing-attribute]
            kernel.configs,
            grid,
        )
        namespace: dict[str, Any] = {}
        exec(code, namespace)
        grid_fn = namespace[fn_name]

    if tma_descriptor_metadata:
        # as we need to launch the kernel here, we "unwrap" the
        # tma_descriptor_metadata, create the TMA descriptors
        # from it, and replace the tensors in the kwargs by the
        # corresponding TMA descriptors before launching
        kwargs = kwargs.copy()
        for k, v in tma_descriptor_metadata.items():
            tensor = kwargs[k]
            if (exp_meta := maybe_unpack_tma_experimental_metadata(v)) is not None:
                from triton.tools.experimental_descriptor import (
                    create_1d_tma_descriptor,
                    create_2d_tma_descriptor,
                )

                dims, block_dims, element_size = exp_meta
                create_tma_descriptor = (
                    create_1d_tma_descriptor
                    if len(dims) == 1
                    else create_2d_tma_descriptor
                )
                kwargs[k] = create_tma_descriptor(
                    tensor.data_ptr(),
                    *dims,
                    *block_dims,
                    element_size,
                )
            else:
                stable_meta = maybe_unpack_tma_stable_metadata(v)
                if stable_meta is None:
                    raise AssertionError(
                        f"Failed to unpack stable TMA metadata for key {k}"
                    )
                from triton.tools.tensor_descriptor import TensorDescriptor

                block_shape = stable_meta[0]

                kwargs[k] = TensorDescriptor.from_tensor(tensor, block_shape)

    # move as many positional arguments from dicts to args as we
    # can to circumvent the bug with the kwargs and pre_/post_hook:
    # https://github.com/triton-lang/triton/issues/5082
    # TODO: remove this when the Triton issue above is fixed
    args = []
    # copy kwargs and constant_args here to
    # avoid mutating the original inputs
    kwargs = kwargs.copy()
    constant_args = constant_args.copy()
    # pyrefly: ignore [missing-attribute]
    for name in kernel.arg_names:
        if name in kwargs:
            args.append(kwargs.pop(name))
        elif name in constant_args:
            args.append(constant_args.pop(name))
        else:
            break

    # pyrefly: ignore [bad-index, index-error]
    kernel[grid_fn](*args, **kwargs, **constant_args)