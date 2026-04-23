def wrapper(*args, **kwargs):
                scalars = [
                    arg
                    for arg in args
                    if isinstance(arg, (int, sympy.Expr))
                    or (isinstance(arg, CppCSEVariable) and not arg.is_vec)
                ]
                vectors = [
                    arg
                    for arg in args
                    if isinstance(arg, CppCSEVariable) and arg.is_vec
                ]
                new_args = list(args)
                if scalars and vectors:
                    new_args = []
                    for arg in args:
                        if isinstance(arg, (int, sympy.Expr)):
                            if isinstance(arg, sympy.Expr) and not arg.is_number:
                                arg = ops.index_expr(arg, torch.int64)
                            else:
                                arg = ops.constant(arg, torch.int64)
                            arg = arg.value if isinstance(arg, OpsValue) else arg
                        new_args.append(arg)

                # DType Promotion
                if vectors:
                    # We have saw several data type mismatch issues related with index_expr in
                    # the lowering phase of torch.int8. torch.int32, torch.int64.
                    # 1. int32 and int64 in test_torchinductor.py::test_max_pool2d_with_indices_backward3_cpu
                    # 2. int8 and int32 in test_torchinductor.py::test_max_pool2d5_cpu
                    # 3. int32 and fp32 in test_torchinductor_dynamic_shapes.py::test_avg_pool2d8_dynamic_shapes_cpu
                    if len(new_args) == 2:
                        new_args = promote_args(new_args)
                    elif func is CppVecOverrides.where:
                        new_args[1:] = promote_args(new_args[1:])

                # Broadcast scalar args to vector
                if scalars and vectors:
                    assert isinstance(V.kernel, CppVecKernel)
                    new_args = [
                        (
                            V.kernel.broadcast(new_arg)
                            if (
                                isinstance(new_arg, CppCSEVariable)
                                and not new_arg.is_vec
                                and func
                                not in [
                                    CppVecOverrides.rand,
                                    CppVecOverrides.randn,
                                    CppVecOverrides.randint64,
                                ]
                            )
                            else new_arg
                        )
                        for new_arg in new_args
                    ]

                if vectors:
                    return func(*new_args, **kwargs)
                else:
                    # fallback to scalar ops
                    scalar_ops = super(CppVecOverrides, self)
                    scalar_func = getattr(scalar_ops, func.__name__)
                    assert scalar_func is not None
                    return scalar_func(*args, **kwargs)