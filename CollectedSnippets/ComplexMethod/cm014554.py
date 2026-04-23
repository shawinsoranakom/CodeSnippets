def generate_out_args_from_schema(
    func: FunctionSchema,
) -> tuple[list[Return], list[Argument]]:
    # More of a sanity check - our existing restrictions on schemas should enforce that
    # mutable schema kinds never return their mutable arguments.
    if any(r.annotation is not None and r.annotation.is_write for r in func.returns):
        raise AssertionError("Mutable schema kinds should not return mutable arguments")

    tensorlike_rets = [r for r in func.returns if r.type.is_tensor_like()]
    if len(tensorlike_rets) == 0:
        raise AssertionError("Expected at least one tensor-like return")

    used_annotations = concatMap(
        lambda a: [] if a.annotation is None else a.annotation.alias_set,
        func.arguments.flat_all,
    )
    valid_annotations = [x for x in string.ascii_lowercase if x not in used_annotations]

    all_rets_are_tensors = all(r.type == BaseType(BaseTy.Tensor) for r in func.returns)

    new_out_args: list[Argument] = []
    # The end result of new_returns is that:
    # - If every return is a plain tensor, then the new returns == the old returns, but with the out= alias annotations added.
    # - Otherwise, none of the out arguments show up in the returns (and we're only left with non-tensor-like returns, if any).
    new_returns: list[Return] = []
    for i, r in enumerate(func.returns):
        if r.type.is_tensor_like():
            new_out = Argument(
                name="out" if len(func.returns) == 1 else f"out{i}",
                type=r.type,
                default=None,
                annotation=Annotation.parse(f"{valid_annotations[i]}!"),
            )
            new_out_args.append(new_out)
            if all_rets_are_tensors:
                # The convention for out= schemas is that they only return their out arguments
                # if the return is a plain Tensor (or if it's a tuple of plain Tensors)
                new_ret = Return(
                    name=None, type=new_out.type, annotation=new_out.annotation
                )
                new_returns.append(new_ret)
        else:
            new_returns.append(r)
    return new_returns, new_out_args