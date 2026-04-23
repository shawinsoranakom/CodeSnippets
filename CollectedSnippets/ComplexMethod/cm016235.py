def generate_state_getter_setter(
    bindings: list[Binding],
    state_vec_type: NamedCType,
) -> tuple[list[str], list[str], str]:
    getter_logic = []
    setter_logic = []

    state_vec = state_vec_type.name
    getter_logic.append(f"{state_vec_type.cpp_type()} {state_vec};")
    if len(bindings) > 0:
        setter_logic.append("auto i = 0;")

    num_exprs = []
    for i, b in enumerate(bindings):
        if not isinstance(b.argument, Argument):
            raise AssertionError(f"Expected Argument, got {type(b.argument)}")
        if b.argument.type.is_list_like():
            # Handle list-likes.
            num_expr = f"{b.name}.size()"
            num_exprs.append(num_expr)
            getter = f"{state_vec}.insert({state_vec}.end(), {b.name}.begin(), {b.name}.end());"
            setter = f"std::copy({state_vec}.begin() + i, {state_vec}.begin() + i + {b.name}.size(), {b.name}.begin());"
        elif isinstance(b.argument.type, OptionalType):
            # Handle optionals.
            num_expr = f"({b.name}.has_value() ? 1 : 0)"
            num_exprs.append(num_expr)
            conditional = f"if({b.name}.has_value())"
            getter = (
                f"{conditional} {state_vec}.insert({state_vec}.end(), *({b.name}));"
            )
            setter = f"{conditional} {b.name} = {state_vec}[i];"
        else:
            num_expr = "1"
            num_exprs.append(num_expr)
            getter = f"{state_vec}.push_back({b.name});"
            setter = f"{b.name} = {state_vec}[i];"

        getter_logic.append(getter)
        setter_logic.append(setter)
        if i < len(bindings) - 1:
            setter_logic.append(f"i += {num_expr};")

    # Reserve / assert based on the total number of items expression.
    num_items = "0" if len(num_exprs) == 0 else " + ".join(num_exprs)
    if len(bindings) > 0:
        getter_logic.insert(1, f"{state_vec}.reserve({num_items});")

    getter_logic.append(f"return {state_vec};")

    return getter_logic, setter_logic, num_items