def _gen_col_aliases(cls, exprs):
        yield from (expr.alias for expr in cls._gen_cols(exprs))