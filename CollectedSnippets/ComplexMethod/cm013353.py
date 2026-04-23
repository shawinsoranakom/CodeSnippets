def error_inputs_diagonal_diag_embed(op_info, device, **kwargs):
    make_arg = partial(make_tensor, device=device, dtype=torch.float32)

    shapes1d = (0, 1, (0,), (1,))
    shapes2d = ((M, L),)
    shapes3d = ((M, S, L),)

    kwargs1d = {}

    kwargs2d = (
        # dim1 == dim2 is not allowed
        dict(dim1=1, dim2=1),
        # out of bounds dims are not allowed
        dict(dim1=10000),
        dict(dim2=10000),
    )

    kwargs3d = kwargs2d

    samples1d = product(shapes1d, kwargs1d)
    samples2d = product(shapes2d, kwargs2d)
    samples3d = product(shapes3d, kwargs3d)

    for shape, kwargs in chain(samples1d, samples2d, samples3d):
        arg = make_arg(shape)
        sample = SampleInput(input=arg, kwargs=kwargs)

        dim1 = kwargs.get("dim1")
        dim2 = kwargs.get("dim2")

        if "diagonal" in op_info.name:
            num_dim = arg.dim()
        elif op_info.name in ("diag_embed", "_refs.diag_embed"):
            # these are valid inputs for diag_embed
            if shape in ((0,), (1,)):
                continue
            num_dim = arg.dim() + 1
        else:
            raise RuntimeError("should be unreachable")

        bound1 = -num_dim
        bound2 = num_dim - 1
        dim_range = range(bound1, bound2 + 1)
        dim1_cond = dim1 and dim1 not in dim_range
        dim2_cond = dim2 and dim2 not in dim_range

        if dim1 == dim2:
            err = f"diagonal dimensions cannot be identical {dim1}, {dim2}"
            yield ErrorInput(sample, error_regex=err, error_type=RuntimeError)
        elif dim1_cond or dim2_cond:
            err_dim = dim1 if dim1_cond else dim2
            err = (
                r"Dimension out of range \(expected to be in range of "
                rf"\[{bound1}, {bound2}\], but got {err_dim}\)"
            )
            yield ErrorInput(sample, error_regex=err, error_type=IndexError)
        else:
            raise RuntimeError("should be unreachable")