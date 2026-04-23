def try_solve(
    expr: sympy.Basic,
    thing: sympy.Basic,
    trials: int = 5,
    floordiv_inequality: bool = True,
) -> tuple[sympy.Rel, sympy.Expr] | None:
    mirror = mirror_rel_op(type(expr))

    # Ignore unsupported expressions:
    #   - Those that are not relational operations
    #   - Those that don't have a mirror (just avoiding unexpected classes)
    if not isinstance(expr, sympy.Rel) or mirror is None:
        log.debug("expression with unsupported type: %s", type(expr))
        return None

    lhs_has_thing = expr.lhs.has(thing)
    rhs_has_thing = expr.rhs.has(thing)

    # Give up when 'thing' appears on both sides of the relational expression.
    # That is because, as is, we assume the thing we are trying to isolate is
    # only on the right-hand side.
    if lhs_has_thing and rhs_has_thing:
        log.debug("thing (%s) found in both sides of expression: %s", thing, expr)
        return None

    # Try considering both LHS and RHS by mirroring the original expression:
    # a < b ==> b > a
    expressions = []

    # Add each version of 'expr' if 'thing' is in its left-hand side.
    if lhs_has_thing:
        expressions.append(expr)
    if rhs_has_thing:
        expressions.append(mirror(expr.rhs, expr.lhs))

    for e in expressions:
        if e is None:
            continue

        if not isinstance(e, sympy.Rel):
            raise AssertionError("expected sympy.Rel")

        for _ in range(trials):
            trial = _try_isolate_lhs(e, thing, floordiv_inequality=floordiv_inequality)
            # Stop if there was no change in this trial.
            if trial == e:
                break
            e = trial  # type: ignore[assignment]

        # Return if we were able to isolate 'thing' on the left-hand side.
        if isinstance(e, sympy.Rel) and e.lhs == thing:
            log.debug("solved: %s ---> %s", expr, e)
            return e, e.rhs

    return None