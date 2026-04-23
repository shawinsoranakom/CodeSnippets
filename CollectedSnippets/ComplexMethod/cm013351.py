def sample_inputs_linalg_norm(
    op_info, device, dtype, requires_grad, *, variant=None, **kwargs
):
    if variant is not None and variant != "subgradient_at_zero":
        raise ValueError(
            f"Unsupported variant, expected variant to be 'subgradient_at_zero' but got: {variant}"
        )

    test_sizes = [
        (S,),
        (0,),
        (S, S),
        (0, 0),
        (S, 0),
        (0, S),
        (S, S, S),
        (0, S, S),
        (S, 0, S),
        (0, 0, 0),
    ]

    vector_ords = (None, 0, 0.5, 1, 2, 3.5, inf, -0.5, -1, -2, -3.5, -inf)
    if dtype in {torch.float16, torch.bfloat16, torch.complex32}:
        # svdvals not supported for low precision dtypes
        matrix_ords = ("fro", inf, -inf, 1, -1)
    else:
        matrix_ords = (None, "fro", "nuc", inf, -inf, 1, -1, 2, -2)

    make_arg = partial(
        make_tensor,
        dtype=dtype,
        device=device,
        requires_grad=requires_grad,
        low=None,
        high=None,
    )

    for test_size in test_sizes:
        is_vector_norm = len(test_size) == 1
        is_matrix_norm = len(test_size) == 2

        # IndexError: amax(): Expected reduction dim 0 to have non-zero size.
        is_valid_for_p2 = is_vector_norm or (test_size[-1] != 0 and test_size[-2] != 0)

        for keepdim in [False, True]:
            if variant != "subgradient_at_zero" and is_valid_for_p2:
                yield SampleInput(make_arg(test_size), keepdim=keepdim)

            if not (is_vector_norm or is_matrix_norm):
                continue

            ords = vector_ords if is_vector_norm else matrix_ords

            for ord in ords:
                if is_vector_norm and test_size[-1] == 0:
                    if ord == np.inf or (ord is not None and ord < 0):
                        # RuntimeError: linalg.vector_norm cannot compute the
                        # {ord} norm on an empty tensor because the operation
                        # does not have an identity
                        continue
                elif is_matrix_norm:
                    dims_to_check = {
                        None: (0,),
                        -1: (1,),
                        -2: (0, 1),
                        -np.inf: (0,),
                    }.get(ord, ())

                    if any(test_size[d] == 0 for d in dims_to_check):
                        # IndexError: amax(): Expected reduction dim {dim} to
                        # have non-zero size.
                        continue

                    no_grad_dims_to_check = {
                        np.inf: (0,),
                        2: (0, 1),
                        1: (1,),
                    }.get(ord, ())

                    if (
                        any(test_size[d] == 0 for d in no_grad_dims_to_check)
                        and requires_grad
                    ):
                        continue

                if variant == "subgradient_at_zero":
                    yield SampleInput(
                        torch.zeros(
                            test_size,
                            dtype=dtype,
                            device=device,
                            requires_grad=requires_grad,
                        ),
                        ord,
                        keepdim=keepdim,
                    )
                else:
                    yield SampleInput(make_arg(test_size), ord, keepdim=keepdim)

                    if ord in ["nuc", "fro"]:
                        yield SampleInput(
                            make_arg(test_size), ord=ord, keepdim=keepdim, dim=(0, 1)
                        )