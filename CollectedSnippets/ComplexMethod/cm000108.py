def dpll_algorithm(
    clauses: list[Clause], symbols: list[str], model: dict[str, bool | None]
) -> tuple[bool | None, dict[str, bool | None] | None]:
    """
    Returns the model if the formula is satisfiable, else ``None``

    This has the following steps:
      1. If every clause in clauses is ``True``, return ``True``.
      2. If some clause in clauses is ``False``, return ``False``.
      3. Find pure symbols.
      4. Find unit symbols.

    >>> formula = Formula([Clause(["A4", "A3", "A5'", "A1", "A3'"]), Clause(["A4"])])
    >>> clauses, symbols = generate_parameters(formula)
    >>> soln, model = dpll_algorithm(clauses, symbols, {})
    >>> soln
    True
    >>> model
    {'A4': True}
    """
    check_clause_all_true = True
    for clause in clauses:
        clause_check = clause.evaluate(model)
        if clause_check is False:
            return False, None
        elif clause_check is None:
            check_clause_all_true = False
            continue

    if check_clause_all_true:
        return True, model

    try:
        pure_symbols, assignment = find_pure_symbols(clauses, symbols, model)
    except RecursionError:
        print("raises a RecursionError and is")
        return None, {}
    p = None
    if len(pure_symbols) > 0:
        p, value = pure_symbols[0], assignment[pure_symbols[0]]

    if p:
        tmp_model = model
        tmp_model[p] = value
        tmp_symbols = list(symbols)
        if p in tmp_symbols:
            tmp_symbols.remove(p)
        return dpll_algorithm(clauses, tmp_symbols, tmp_model)

    unit_symbols, assignment = find_unit_clauses(clauses, model)
    p = None
    if len(unit_symbols) > 0:
        p, value = unit_symbols[0], assignment[unit_symbols[0]]
    if p:
        tmp_model = model
        tmp_model[p] = value
        tmp_symbols = list(symbols)
        if p in tmp_symbols:
            tmp_symbols.remove(p)
        return dpll_algorithm(clauses, tmp_symbols, tmp_model)
    p = symbols[0]
    rest = symbols[1:]
    tmp1, tmp2 = model, model
    tmp1[p], tmp2[p] = True, False

    return dpll_algorithm(clauses, rest, tmp1) or dpll_algorithm(clauses, rest, tmp2)