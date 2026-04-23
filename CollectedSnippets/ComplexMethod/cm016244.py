def save_variables(
        saved_variables: Sequence[SavedAttribute],
        is_output: bool,
        guard_for: Callable[[SavedAttribute], str | None] = lambda name: None,
    ) -> Sequence[str]:
        # assign the saved variables to the generated grad_fn
        stmts: list[str] = []
        for arg in sorted(saved_variables, key=lambda sa: str(sa.nctype.name)):
            name = (
                arg.nctype.name.name
                if isinstance(arg.nctype.name, SpecialArgName)
                else arg.nctype.name
            )
            foreacharg: Argument | None = None
            is_foreacharg_list_type: bool = False
            type = arg.nctype.type
            expr = arg.expr
            stmts_prepend = None
            if is_inplace_foreach and info is not None:
                # todo(crcrpar): See if we can add some check e.g. `assert foreacharg is not None`.
                # for now the example assert would fail.
                name_to_query = name.split("_scalar_type")[0]
                if name_to_query in refargname2inplace_foreacharg:
                    foreacharg = refargname2inplace_foreacharg[name_to_query]
                    is_foreacharg_list_type = isinstance(foreacharg.type, ListType)
                if foreacharg is not None:
                    name_in_expr = (
                        f"{foreacharg.name}{'[i]' if is_foreacharg_list_type else ''}"
                    )
                    src_name = name
                    if "_scalar_type" in src_name:
                        split_src_name = src_name.split("_scalar_type")
                        if len(split_src_name) != 2:
                            raise AssertionError(
                                f"expected 2 parts after split, got {len(split_src_name)}: {split_src_name}"
                            )
                        src_name = split_src_name[0]
                    expr = expr.replace(src_name, name_in_expr)
            if (
                type == BaseCType(tensorT)
                or type == OptionalCType(BaseCType(tensorT))
                or type == MutRefCType(OptionalCType(BaseCType(tensorT)))
                or (is_output and type == BaseCType(scalarT))
            ):
                # note(crcrpar): Here `expr` is generated from scratch, `arg.expr` is ignored.
                var = name
                name += "_"
                if var == "self" and inplace:
                    original_self_var = (
                        "original_self"
                        if not is_inplace_foreach
                        else "original_selfs[i]"
                    )
                    self_var = var if not is_inplace_foreach else var + "[i]"
                    stmts_prepend = f"if (!{original_self_var}.has_value()) {original_self_var} = {self_var}.clone()"
                    var = f"{original_self_var}.value()"
                    if is_output:
                        raise AssertionError(
                            "is_output should be False when var == 'self' and inplace"
                        )
                if inplace and is_output:
                    if name != "result_":
                        raise AssertionError(
                            f"expected name to be 'result_' for inplace output, got {name}"
                        )
                    var = (
                        "self[i]"
                        if is_inplace_foreach or is_foreacharg_list_type
                        else "self"
                    )
                    is_inplace_view = f"{var}.is_view()"
                    expr = f"SavedVariable({var}, {str(is_output).lower()}, {is_inplace_view})"
                else:
                    expr = f"SavedVariable({var}, {str(is_output).lower()})"
                    if foreacharg is not None and "original_selfs" not in expr:
                        # pyrefly: ignore [unbound-name]
                        expr = expr.replace(src_name, name_in_expr)
            elif (
                type == BaseCType(tensorListT)
                or type == ListCType(OptionalCType(BaseCType(tensorT)))
                or type == BaseCType(iTensorListRefT)
                or type == VectorCType(BaseCType(tensorT))
            ):
                # See Note [nuanced return type of out-of-place foreach functions]
                if type == VectorCType(BaseCType(tensorT)):
                    if not (is_foreach and is_output):
                        raise AssertionError(
                            f"VectorCType(BaseCType(tensorT)) requires is_foreach and is_output, "
                            f"got is_foreach={is_foreach}, is_output={is_output}"
                        )
                expr = f"make_saved_variable_list({name}, {str(is_foreach and is_output).lower()})"
                name += "_"
            elif type == BaseCType(intArrayRefT):
                expr = expr + ".vec()"
            elif type == BaseCType(symIntArrayRefT):
                expr = expr + ".vec()"
            elif type == BaseCType(stringT):
                expr = f"std::string({expr})"
            elif type == OptionalCType(BaseCType(stringT)):
                expr = f"{expr}.has_value() ? ::std::optional<std::string>(std::string({expr}.value())) : ::std::nullopt"
            elif type == ArrayRefCType(
                elem=BaseCType(type=BaseCppType(ns="at", name="Scalar"))
            ):
                expr = expr + ".vec()"

            guard = guard_for(arg)
            if guard is None:
                if stmts_prepend:
                    stmts.append(f"{stmts_prepend};")
                stmts.append(f"grad_fn->{name} = {expr};")
            else:
                stmts.append(f"if ({guard}) {{")
                if stmts_prepend:
                    stmts.append(f"  {stmts_prepend};")
                stmts.append(f"  grad_fn->{name} = {expr};")
                stmts.append("}")
        return stmts