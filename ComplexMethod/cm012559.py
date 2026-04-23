def deduce_output_dtype_by_name(
    op_name: str,
    *args: Any,
    **kwargs: Any,
) -> torch.dtype | None:
    """
    Given op name and a list of input dtypes, deduce the output dtype
    """
    if op_name in boolean_ops():
        return torch.bool
    elif op_name in (
        "to_dtype",
        "index_expr",
    ):
        return kwargs["dtype"] if "dtype" in kwargs else args[-1]
    elif op_name in (
        "rand",
        "randn",
    ):
        return torch.float
    elif op_name in (
        "get_index",
        "randint64",
        "load_seed",
    ):
        return torch.int64
    elif op_name == "reduction":
        return kwargs["dtype"] if "dtype" in kwargs else args[1]
    elif op_name == "constant":
        return kwargs["dtype"] if "dtype" in kwargs else args[-1]
    elif op_name in (
        "load",
        "store",
        "store_reduction",
    ):
        buf_name = args[1]
        return V.graph.get_dtype(buf_name)  # type: ignore[arg-type]
    elif op_name == "to_dtype_bitcast":
        return kwargs["dtype"] if "dtype" in kwargs else args[-2]
    return None