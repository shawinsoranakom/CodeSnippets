def find_unit_clauses(
    clauses: list[Clause],
    model: dict[str, bool | None],  # noqa: ARG001
) -> tuple[list[str], dict[str, bool | None]]:
    """
    Returns the unit symbols and their values to satisfy clause.

    Unit symbols are symbols in a formula that are:
      - Either the only symbol in a clause
      - Or all other literals in that clause have been assigned ``False``

    This has the following steps:
      1. Find symbols that are the only occurrences in a clause.
      2. Find symbols in a clause where all other literals are assigned ``False``.
      3. Assign ``True`` or ``False`` depending on whether the symbols occurs in
         normal or complemented form respectively.

    >>> clause1 = Clause(["A4", "A3", "A5'", "A1", "A3'"])
    >>> clause2 = Clause(["A4"])
    >>> clause3 = Clause(["A3"])
    >>> clauses, symbols = generate_parameters(Formula([clause1, clause2, clause3]))
    >>> unit_clauses, values = find_unit_clauses(clauses, {})
    >>> unit_clauses
    ['A4', 'A3']
    >>> values
    {'A4': True, 'A3': True}
    """
    unit_symbols = []
    for clause in clauses:
        if len(clause) == 1:
            unit_symbols.append(next(iter(clause.literals.keys())))
        else:
            f_count, n_count = 0, 0
            for literal, value in clause.literals.items():
                if value is False:
                    f_count += 1
                elif value is None:
                    sym = literal
                    n_count += 1
            if f_count == len(clause) - 1 and n_count == 1:
                unit_symbols.append(sym)
    assignment: dict[str, bool | None] = {}
    for i in unit_symbols:
        symbol = i[:2]
        assignment[symbol] = len(i) == 2
    unit_symbols = [i[:2] for i in unit_symbols]

    return unit_symbols, assignment