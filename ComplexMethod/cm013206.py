def sample_inputs_index(op_info, device, dtype, requires_grad, reference=False, **kwargs):
    # target.index_add(dim, idx, source, *, alpha=1)
    add = "index_add" in op_info.name
    # target.index_copy(dim, idx, source)
    copy = "index_copy" in op_info.name
    # target.index_fill(dim, idx, value)
    fill = "index_fill" in op_info.name

    # Extended reference inputs. We generate that exercise atomic adds / writing
    # several times to one location
    if reference:
        make_arg = partial(torch.ones, device=device, dtype=dtype, requires_grad=requires_grad)
        make_idx = partial(torch.zeros, device=device, dtype=torch.int64)
    else:
        make_arg = partial(make_tensor, device=device, dtype=dtype, requires_grad=requires_grad)
        # idx They need to be different for copy and add to be deterministic
        if copy or add:
            make_idx = partial(torch.randperm, device=device, dtype=torch.int64)
        else:
            def make_idx(n):
                return make_tensor((n,), device=device, dtype=torch.int64, low=0, high=n)

    shapes = [(), (1,), (S, S)]
    # extra parameter for add
    if add:
        if dtype == torch.bool:
            alphas = (True, False)
        else:
            alphas = (-1, 0, 2)
    else:
        alphas = (None,)

    if fill:
        # A weird number to catch errors.
        # The former one tests `index_fill.int_Scalar`, and the latter one tests `index_fill.int_Tensor`.
        values = (make_arg((1,)).item(), make_arg(()))
    else:
        values = (None,)

    for shape, alpha, value in product(shapes, alphas, values):
        t = make_arg(shape)
        args = []

        # dim. We handle the scalar case
        dim = -1 if t.ndim == 2 else 0
        args.append(dim)

        idx = make_idx(t.shape[dim] if t.ndim != 0 else 1)
        args.append(idx)

        # source
        if copy or add:
            args.append(make_arg(shape))
        elif fill:
            args.append(value)

        args = tuple(args)
        kwargs = {} if alpha is None else {"alpha": alpha}

        yield SampleInput(t, args=args, kwargs=kwargs)