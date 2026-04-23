def track_symint(
            source: Source, val: IntLikeType, constraint: DimConstraint = None
        ) -> None:
            log.debug(
                "track_symint %s %s %s",
                LazyString(lambda: source.name),
                val,
                constraint,
            )
            if isinstance(val, SymInt) and not is_symbolic(val):
                raise AssertionError("val must be symbolic if it is a SymInt")

            if isinstance(val, SymInt) and val.node.maybe_as_int() is not None:
                val = val.node.maybe_as_int()

            if isinstance(val, SymInt):
                s = val.node.expr
                if isinstance(s, sympy.Symbol):
                    symbol_to_source[s].append(source)
                    if constraint is not None and not isinstance(
                        constraint, RelaxedUnspecConstraint
                    ):
                        symbol_to_constraints[s].add(constraint)
                else:
                    constraint_violated = False
                    if isinstance(constraint, StrictMinMaxConstraint):
                        # try inferring the ranges of the expr s
                        sym_vrs = {
                            x: self.var_to_range.get(x, None) for x in s.free_symbols
                        }
                        if any(vr is None for vr in sym_vrs.values()):
                            # some of the free symbols in s don't have ranges
                            constraint_violated = True
                    elif isinstance(constraint, RelaxedUnspecConstraint):
                        if s.is_number:
                            i = int(s)
                            # Don't complain about 0/1 specialization, we
                            # expect to have to compile in this case anyway
                            if i not in (0, 1):
                                constraint_violated = True
                    if constraint_violated:
                        if constraint is None:
                            raise AssertionError("constraint must not be None")

                        def hint(s: sympy.Expr) -> str:
                            sexpr = py_printer.doprint(s)
                            return f"{sexpr}."

                        var_with_range = self._render_range_for_constraint_violation(
                            source, constraint
                        )
                        msg = (
                            f"Not all values of {var_with_range} are valid because "
                            f"{self._debug_name(source)} was inferred to be equal to "
                        )
                        record_constraint_violation(
                            constraint.warn_only,
                            self._debug_name(source),
                            msg,
                            hint=functools.partial(hint, s),
                        )

                input_guards.append((source, s))
            else:
                s = sympy.Integer(val)
                input_guards.append((source, s))
                constraint_violated = False
                if isinstance(constraint, StrictMinMaxConstraint):
                    if not (
                        s == constraint.vr.lower == constraint.vr.upper
                    ):  # allow static constraints
                        constraint_violated = True
                elif isinstance(constraint, RelaxedUnspecConstraint):
                    # Don't complain about 0/1 specialization, we
                    # expect to have to compile in this case anyway
                    if val not in (0, 1):
                        constraint_violated = True
                if constraint_violated:
                    if constraint is None:
                        raise AssertionError("constraint must not be None")
                    var_with_range = self._render_range_for_constraint_violation(
                        source, constraint
                    )
                    user_stack = self.specialization_stacks.get(source, None)
                    msg = (
                        f"You marked {self._debug_name(source)} as dynamic but your code "
                        f"specialized it to be a constant ({val}). If you're using mark_dynamic, "
                        f"either remove it or use maybe_mark_dynamic. If you're using Dim.DYNAMIC, "
                        f"replace it with either Dim.STATIC or Dim.AUTO."
                        + (
                            "\n\nUser stack:\n" + "".join(user_stack.format())
                            if user_stack
                            else ""
                        )
                    )
                    record_constraint_violation(
                        constraint.warn_only, self._debug_name(source), msg
                    )