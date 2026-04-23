def mutates_and_returns_first_arg(op: OpOverload):
    """Check if an op is an inplace aten op, i.e. it mutates and returns the first arg.

    TODO: torchgen/model.py's FunctionSchema.parse is the source of truth for this,
    but not all PyTorch builds have torchgen (due to the yaml dependency being weird).
    Figure this out.

    Example: add_(Tensor(a!) x, Tensor y) -> Tensor(a)
    """
    if op.namespace != "aten":
        return False
    schema = op._schema
    if len(schema.returns) != 1:
        return False
    if schema.returns[0].alias_info is None:
        return False
    alias_set = schema.returns[0].alias_info.after_set
    if len(alias_set) != 1:
        return False
    loc = next(iter(alias_set))
    if len(schema.arguments) < 1:
        return False
    first_arg = schema.arguments[0]
    if first_arg.alias_info is None:
        return False
    if not first_arg.alias_info.is_write:
        return False
    alias_set = first_arg.alias_info.after_set
    if len(alias_set) != 1:
        return False
    if loc != next(iter(alias_set)):
        return False
    for arg in schema.arguments[1:]:
        if arg.alias_info is not None:
            return False
    return True