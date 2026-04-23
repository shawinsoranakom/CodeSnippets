def get_fallback_sql(self, compiler, connection):
        # Process right-hand-side to trigger sanitization.
        self.process_rhs(compiler, connection)
        # e.g.: (a, b, c) < (x, y, z) as SQL:
        # WHERE a < x OR (a = x AND (b < y OR (b = y AND c < z)))
        lookups = itertools.cycle([LessThan, Exact])
        connectors = itertools.cycle([OR, AND])
        cols_list = [col for col in self.lhs for _ in range(2)]
        vals_list = [val for val in self.rhs for _ in range(2)]
        cols_iter = iter(cols_list[:-1])
        vals_iter = iter(vals_list[:-1])
        col = next(cols_iter)
        val = next(vals_iter)
        lookup = next(lookups)
        connector = next(connectors)
        root = node = WhereNode([lookup(col, val)], connector=connector)

        for col, val in zip(cols_iter, vals_iter):
            lookup = next(lookups)
            connector = next(connectors)
            child = WhereNode([lookup(col, val)], connector=connector)
            node.children.append(child)
            node = child

        return root.as_sql(compiler, connection)