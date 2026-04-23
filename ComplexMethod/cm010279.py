def apply_fixes(path, dim, dummy):
        if dim is None or isinstance(dim, int):  # not dynamic
            return dim
        elif dim.__name__ in shape_fixes:  # directly fix
            fix = shape_fixes[dim.__name__]
            if isinstance(fix, sympy.Expr):  # now derived or related
                if str(fix) in derived_dim_cache:
                    return derived_dim_cache[str(fix)]
                else:
                    symbol = next(iter(fix.free_symbols))
                    # try to locate symbol
                    if symbol.name in shape_fixes:
                        root = shape_fixes[symbol.name]
                    else:
                        if symbol.name not in name_to_dim:
                            raise AssertionError(
                                f"symbol.name {symbol.name!r} not found in name_to_dim"
                            )
                        root = name_to_dim[symbol.name]
                    # figure out value of fix
                    modulus, remainder = sympy.polys.polytools.div(fix, symbol)
                    dim = root
                    if modulus != 1:
                        dim = int(modulus) * dim
                    if remainder != 0:
                        dim = dim + int(remainder)
                    # pyrefly: ignore [unsupported-operation]
                    derived_dim_cache[str(fix)] = dim
                    return dim
            else:
                return fix
        elif isinstance(dim, _DerivedDim) and dim.root.__name__ in shape_fixes:  # type: ignore[attr-defined]
            if dim.__name__ in derived_dim_cache:
                return derived_dim_cache[dim.__name__]
            else:  # evaluate new derived value based on root
                _dim = dim.fn(shape_fixes[dim.root.__name__])  # type: ignore[attr-defined]
                derived_dim_cache[dim.__name__] = _dim
                return _dim
        return dim