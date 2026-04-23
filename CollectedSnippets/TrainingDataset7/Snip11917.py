def __iter__(self):
        queryset = self.queryset
        query = queryset.query
        compiler = query.get_compiler(queryset.db)
        return compiler.results_iter(
            tuple_expected=True,
            chunked_fetch=self.chunked_fetch,
            chunk_size=self.chunk_size,
        )