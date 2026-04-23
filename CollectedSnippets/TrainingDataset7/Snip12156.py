def results_iter(
        self,
        results=None,
        tuple_expected=False,
        chunked_fetch=False,
        chunk_size=GET_ITERATOR_CHUNK_SIZE,
    ):
        """Return an iterator over the results from executing this query."""
        if results is None:
            results = self.execute_sql(
                MULTI, chunked_fetch=chunked_fetch, chunk_size=chunk_size
            )
        fields = [s[0] for s in self.select[0 : self.col_count]]
        converters = self.get_converters(fields)
        rows = chain.from_iterable(results)
        if converters:
            rows = self.apply_converters(rows, converters)
        if self.has_composite_fields(fields):
            rows = self.composite_fields_to_tuples(rows, fields)
        if tuple_expected:
            rows = map(tuple, rows)
        return rows