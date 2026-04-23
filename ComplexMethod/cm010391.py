def get_tma_stores(
    functions: dict[str, dict[Intermediate, list[Op]]], fn_name: str
) -> set[Intermediate | Param]:
    """
    Identifies all intermediates and parameters that are written to by a
    `tt.experimental_descriptor_store`. It tracks only the specific values
    written to via experimental_descriptor_store and the input values to
    `tt.reinterpret_tensor_descriptor` used to construct the direct inputs
    to tt.experimental_descriptor_store - not any recursive values
    used to construct those values.

    For example: for
      tt.reinterpret_tensor_descriptor(Intermediate(idx=0), ...)
      Intermediate(idx=1) = tt.experimental_descriptor_store(Intermediate(idx=0), ...)
    this function will return [Intermediate(idx=0), Intermediate(idx=1)],

    However
      Intermediate(idx=4) = arith.addptr(Intermediate(idx=2), Intermediate(idx=3))
      Intermediate(idx=5) = tt.experimental_descriptor_store(Intermediate(idx=4), ...)
      tt.experimental_descriptor_store(Intermediate(idx=5), ...)
    this function will mark only idx=4 and idx=5 (but not idx=2 or idx=3)

    If an intermediate/parameter is passed into a function and is written to
    via experimental_descriptor_store within that function, the argument to the
    function will also be marked.
    """

    result: set[Intermediate | Param] = set()

    ops = functions[fn_name]
    for op_list in ops.values():
        for op in op_list:
            if op.name == "tt.call":
                if op.fn_call_name not in functions:
                    raise AssertionError(
                        f"Function {op.fn_call_name} not found in functions for TMA stores"
                    )
                # pyrefly: ignore [bad-argument-type]
                tma_stores = get_tma_stores(functions, op.fn_call_name)
                for i, inp in enumerate(op.args):
                    if Param(idx=i) in tma_stores:
                        result.add(inp)
            elif op.name == "tt.experimental_descriptor_store":
                if len(op.args) < 1:
                    raise AssertionError(
                        f"tt.experimental_descriptor_store expected at least 1 arg, got {len(op.args)}"
                    )
                result.add(op.args[0])
            elif op.name == "tt.descriptor_store":
                if len(op.args) < 1:
                    raise AssertionError(
                        f"tt.descriptor_store expected at least 1 arg, got {len(op.args)}"
                    )
                result.add(op.args[0])

    for val in list(result):
        if val in ops:
            if not isinstance(val, Intermediate):
                continue
            for op in ops[val]:
                if op.name == "tt.reinterpret_tensor_descriptor":
                    if len(op.args) < 1:
                        raise AssertionError(
                            "tt.reinterpret_tensor_descriptor expected at least 1 arg, "
                            f"got {len(op.args)}"
                        )
                    result.add(op.args[0])

    return result