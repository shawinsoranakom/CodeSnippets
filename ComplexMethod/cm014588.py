def extract_mm_shapes_from_loader(
    loader: OperatorInputsLoader,
) -> list[tuple[int, int, int, torch.dtype, torch.dtype]]:
    """Extract matrix multiplication shapes from an OperatorInputsLoader using deserialize_args with FakeTensorMode."""
    shapes = []

    # Matrix multiplication operators to look for
    mm_operators = ["aten.mm.default", "aten.addmm.default", "aten.bmm.default"]

    # Use FakeTensorMode to avoid instantiating actual tensors
    with FakeTensorMode():
        for op_name in mm_operators:
            if op_name not in loader.operator_db:
                continue

            # Count shapes extracted from this operator
            shape_count = 0

            # Access the raw string data directly from operator_db and reuse existing parsing
            for input_str in loader.operator_db[op_name]:
                try:
                    # Use deserialize_args to parse inputs - will create fake tensors
                    args, kwargs = deserialize_args(input_str)

                    if op_name == "aten.mm.default":
                        # mm(input, mat2) -> result
                        if len(args) >= 2:
                            a, b = args[0], args[1]
                            if isinstance(a, torch.Tensor) and isinstance(
                                b, torch.Tensor
                            ):
                                a_shape, a_dtype = tuple(a.shape), a.dtype
                                b_shape, b_dtype = tuple(b.shape), b.dtype
                                if len(a_shape) == 2 and len(b_shape) == 2:
                                    m, k = a_shape
                                    k2, n = b_shape
                                    if k == k2:  # Valid matrix multiplication
                                        shapes.append((m, k, n, a_dtype, b_dtype))
                                        shape_count += 1

                    elif op_name == "aten.addmm.default":
                        # addmm(bias, input, mat2) -> result
                        if len(args) >= 3:
                            _, a, b = args[0], args[1], args[2]
                            if isinstance(a, torch.Tensor) and isinstance(
                                b, torch.Tensor
                            ):
                                a_shape, a_dtype = tuple(a.shape), a.dtype
                                b_shape, b_dtype = tuple(b.shape), b.dtype
                                if len(a_shape) == 2 and len(b_shape) == 2:
                                    m, k = a_shape
                                    k2, n = b_shape
                                    if k == k2:  # Valid matrix multiplication
                                        shapes.append((m, k, n, a_dtype, b_dtype))
                                        shape_count += 1

                    elif op_name == "aten.bmm.default":
                        # bmm(input, mat2) -> result (batch matrix multiplication)
                        if len(args) >= 2:
                            a, b = args[0], args[1]
                            if isinstance(a, torch.Tensor) and isinstance(
                                b, torch.Tensor
                            ):
                                a_shape, a_dtype = tuple(a.shape), a.dtype
                                b_shape, b_dtype = tuple(b.shape), b.dtype
                                if len(a_shape) == 3 and len(b_shape) == 3:
                                    batch1, m, k = a_shape
                                    batch2, k2, n = b_shape
                                    if (
                                        batch1 == batch2 and k == k2
                                    ):  # Valid batch matrix multiplication
                                        shapes.append((m, k, n, a_dtype, b_dtype))
                                        shape_count += 1

                except Exception:
                    # Skip invalid inputs
                    continue

            print(f"    Extracted {shape_count} shapes from {op_name}")

    return shapes