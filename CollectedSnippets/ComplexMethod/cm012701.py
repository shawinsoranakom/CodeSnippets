def codegen_symbol(
            sym_or_exp: sympy.Symbol | sympy.Expr,
            base_name: str,
            name_fn: Callable[[str], str],
            dim: int,
        ):
            if isinstance(sym_or_exp, sympy.Symbol):
                if sym_or_exp in bound_vars:
                    return
                code.writeline(f"int64_t {sym_or_exp} = {name_fn(base_name)}[{dim}];")
                bound_vars.add(sym_or_exp)
            elif isinstance(sym_or_exp, sympy.Expr):
                undefined_symbols = [
                    sym for sym in sym_or_exp.free_symbols if sym not in bound_vars
                ]
                if len(undefined_symbols) != 1:
                    # Skip if expression contains no symbols or if multiple
                    # symbols exists since we assume each base symbol is defined
                    # by other codegen_symbol calls.
                    return

                from torch.utils._sympy.solve import try_solve

                free_symbol = undefined_symbols.pop()
                base_name = name_fn(base_name)
                # Use a size symbol to solve the free symbol
                size_symbol = sympy.Symbol(f"{base_name}_{dim}", integer=True)
                code.writeline(f"int64_t {size_symbol} = {base_name}[{dim}];")
                solution = try_solve(sympy.Eq(sym_or_exp, size_symbol), free_symbol)
                if solution is not None:
                    code.writeline(f"int64_t {free_symbol} = {cexpr(solution[1])};")
                    bound_vars.add(free_symbol)
                else:
                    raise AssertionError(
                        str(sympy.Eq(sym_or_exp, size_symbol)) + " is not solvable"
                    )