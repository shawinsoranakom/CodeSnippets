def composite_fields_to_tuples(self, rows, expressions):
        col_pair_slices = [
            slice(i, i + len(expression))
            for i, expression in enumerate(expressions)
            if isinstance(expression, ColPairs)
        ]

        for row in map(list, rows):
            for pos in col_pair_slices:
                row[pos] = (tuple(row[pos]),)

            yield row