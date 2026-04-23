def find_pure_symbols(
    clauses: list[Clause], symbols: list[str], model: dict[str, bool | None]
) -> tuple[list[str], dict[str, bool | None]]:
    """
    | Return pure symbols and their values to satisfy clause.
    | Pure symbols are symbols in a formula that exist only in one form,
    | either complemented or otherwise.
    | For example,
    |   {{A4 , A3 , A5' , A1 , A3'} , {A4} , {A3}} has pure symbols A4, A5' and A1.

    This has the following steps:
      1. Ignore clauses that have already evaluated to be ``True``.
      2. Find symbols that occur only in one form in the rest of the clauses.
      3. Assign value ``True`` or ``False`` depending on whether the symbols occurs
         in normal or complemented form respectively.

    >>> formula = Formula([Clause(["A1", "A2'", "A3"]), Clause(["A5'", "A2'", "A1"])])
    >>> clauses, symbols = generate_parameters(formula)
    >>> pure_symbols, values = find_pure_symbols(clauses, symbols, {})
    >>> pure_symbols
    ['A1', 'A2', 'A3', 'A5']
    >>> values
    {'A1': True, 'A2': False, 'A3': True, 'A5': False}
    """
    pure_symbols = []
    assignment: dict[str, bool | None] = {}
    literals = []

    for clause in clauses:
        if clause.evaluate(model):
            continue
        for literal in clause.literals:
            literals.append(literal)

    for s in symbols:
        sym = s + "'"
        if (s in literals and sym not in literals) or (
            s not in literals and sym in literals
        ):
            pure_symbols.append(s)
    for p in pure_symbols:
        assignment[p] = None
    for s in pure_symbols:
        sym = s + "'"
        if s in literals:
            assignment[s] = True
        elif sym in literals:
            assignment[s] = False
    return pure_symbols, assignment