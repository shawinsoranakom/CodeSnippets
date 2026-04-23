def register_element_ops():
    binary_op_list = [
        ["mul", operator.mul],
        ["add", operator.add],
        ["sub", operator.sub],
        ["div", lambda a, b: a / (b + 1e-4)],
        [
            "pow",
            torch.pow,
            np.power,
        ],  # no fuson triggered
        ["max", torch.max, np.maximum],
        ["min", torch.min, np.minimum],
    ]

    unary_op_list = [
        ["erf", torch.erf, scipy.special.erf],
        ["exp", torch.exp, np.exp],
        ["sin", torch.sin, np.sin],
        ["cos", torch.cos, np.cos],
        ["rand_like", torch.rand_like, lambda x: np.random.rand(*x.shape)],
    ]

    for split_input, binary_op in itertools.product([True, False], binary_op_list):
        # Make a copy of ElementBench
        if len(binary_op) == 2:
            [op_str, op_pt_func] = binary_op
            op_np_func = op_pt_func
        elif len(binary_op) == 3:
            [op_str, op_pt_func, op_np_func] = binary_op
        split_str = "split" if split_input else "shared"
        op_str = split_str + "_" + op_str
        bm_cls = type("ElementBench_" + op_str, (ElementBench,), {})
        bm_cls.op_str = op_str
        bm_cls.binary_op_pt_func = op_pt_func
        bm_cls.binary_op_np_func = op_np_func
        bm_cls.split_input = split_input
        benchmark.register_benchmark_class(bm_cls)

    for split_input, unary_op in itertools.product([True, False], unary_op_list):
        # Make a copy of ElementBench
        if len(unary_op) == 2:
            [op_str, op_pt_func] = unary_op
            op_np_func = op_pt_func
        elif len(unary_op) == 3:
            [op_str, op_pt_func, op_np_func] = unary_op
        split_str = "split" if split_input else "shared"
        op_str = split_str + "_" + op_str
        bm_cls = type("ElementBench_" + op_str, (ElementBench,), {})
        bm_cls.op_str = op_str
        bm_cls.unary_op_pt_func = op_pt_func
        bm_cls.unary_op_np_func = op_np_func
        bm_cls.split_input = split_input
        benchmark.register_benchmark_class(bm_cls)