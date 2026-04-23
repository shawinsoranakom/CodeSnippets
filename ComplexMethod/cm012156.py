def is_b2b_gemm_good_on(
    is_left_assoc: bool,
    A_node: torch.fx.Node,
    B_node: torch.fx.Node,
    C_node: torch.fx.Node,
) -> bool:
    """
    checks whether the sizes are good for b2b_gemm
    """
    # basic checks
    if not all(["val" in A_node.meta, "val" in B_node.meta, "val" in C_node.meta]):
        return False
    fake_tensors = (
        A_node.meta["val"],
        B_node.meta["val"],
        C_node.meta["val"],
    )  # torch._subclasses.fake_tensor.FakeTensor

    A, B, C = fake_tensors

    def check_all_attr_true(objects, attr):
        return all(hasattr(obj, attr) and getattr(obj, attr) for obj in objects)

    if not check_all_attr_true(fake_tensors, "is_cuda") and not check_all_attr_true(
        fake_tensors, "is_xpu"
    ):
        return False
    if not all([len(A.shape) == 2, len(B.shape) == 2, len(C.shape) == 2]):
        return False
    if not ((A.shape[1] == B.shape[0]) and (B.shape[1] == C.shape[0])):
        return False
    # size checks: we only dispatch to B2B-GEMM when the average load ratio is > 1
    M, N = A.shape
    O, P = C.shape
    ratios = []
    if is_left_assoc:
        for config in b2b_gemm_configs:
            ratio = load_ratio_left(
                M,
                N,
                O,
                P,
                config["BLOCK_SIZE_M"],
                config["BLOCK_SIZE_N"],
                config["BLOCK_SIZE_O"],
                config["BLOCK_SIZE_P"],
            )
            ratios.append(ratio)
    else:
        for config in b2b_gemm_configs:
            ratio = load_ratio_right(
                M,
                N,
                O,
                P,
                config["BLOCK_SIZE_M"],
                config["BLOCK_SIZE_N"],
                config["BLOCK_SIZE_O"],
                config["BLOCK_SIZE_P"],
            )
            ratios.append(ratio)
    ratios.sort(reverse=True)
    average_ratio = 1.0
    for r in ratios[:3]:  # top 3 choices
        average_ratio *= r
    average_ratio = average_ratio ** (1 / 3)
    return (
        average_ratio > 1
    )