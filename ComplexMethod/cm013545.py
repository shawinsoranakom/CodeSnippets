def issue_guard(guard: ShapeGuard) -> None:
            expr = self.simplify(guard.expr)

            # Avoid re-issuing the same guard.
            if expr in issued:
                return

            issued.add(expr)

            try:
                is_trivial = False
                if any(
                    is_dim(source)
                    for s in expr.free_symbols
                    for source in symbol_to_source[s]
                ):
                    if self.dim_constraints is None:
                        raise AssertionError("dim_constraints must not be None")
                    is_trivial = self.dim_constraints.add(expr)

                for exprs, printer, lang in zip(all_exprs, printers, langs):
                    guard_expr = printer.doprint(expr)
                    if lang == "verbose_python":
                        guard_expr = f"{guard_expr}  # {guard.sloc}"
                    exprs.append(guard_expr)

                self._add_target_expr(expr)
                # A non-relational constraint on a single sizevar can violate
                # a constraint
                if not is_trivial and len(expr.free_symbols) == 1:
                    symbol = next(iter(expr.free_symbols))
                    source = symbol_to_source[symbol][0]
                    constraints = symbol_to_constraints[symbol]
                    for c in constraints:
                        if isinstance(c, StrictMinMaxConstraint):
                            var_with_range = (
                                self._render_range_for_constraint_violation(source, c)
                            )
                            msg = (
                                f"Not all values of {var_with_range} "
                                f"satisfy the generated guard {py_printer.doprint(expr)}."
                            )
                            record_constraint_violation(
                                c.warn_only, self._debug_name(source), msg
                            )
                        elif isinstance(c, RelaxedUnspecConstraint):
                            # This is fine, we allow guards here as long as it
                            # didn't constrain it to one value  (we don't
                            # actually know this; this depends on our
                            # ValueRanges reasoning capability)
                            pass
                        else:
                            raise AssertionError(f"unrecognized constraint {c}")
            except Exception:
                self.log.warning("Failing guard allocated at %s", guard.sloc)
                raise