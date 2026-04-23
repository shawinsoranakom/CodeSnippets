def _compare_objs(obj1, obj2, skip: Sequence = ("logitsprocs", "batch_update_builder")):
    attrs = inspect.getmembers(obj1, lambda a: not (inspect.isroutine(a)))
    attr_names = set(
        [a[0] for a in attrs if not (a[0].startswith("__") and a[0].endswith("__"))]
    )
    for attr_name in attr_names:
        if attr_name in skip:
            continue

        a = getattr(obj1, attr_name)
        b = getattr(obj2, attr_name)

        is_same = False
        if isinstance(a, torch.Tensor):
            if a.numel() == 0 or b.numel() == 0:
                is_same = a.numel() == 0 and b.numel() == 0
            elif torch.allclose(a, b):
                is_same = True
        elif isinstance(a, np.ndarray):
            if np.allclose(a, b):
                is_same = True
        elif isinstance(a, MultiGroupBlockTable):
            for a_i, b_i in zip(a.block_tables, b.block_tables):
                _compare_objs(a_i, b_i)
            is_same = True
        elif isinstance(a, (BlockTable, SamplingMetadata, PoolingMetadata)):
            _compare_objs(a, b)
            is_same = True  # if we make it here must be same
        elif a == b:
            is_same = True
        elif isinstance(a, CpuGpuBuffer):
            is_same = np.allclose(a.np, b.np) and torch.allclose(a.gpu, b.gpu)
        assert is_same, (
            f"Attribute {attr_name} is different in {obj1} and {obj2}: {a} != {b}"
        )