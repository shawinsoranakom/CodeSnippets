def get_group_by_cols(self):
        if not self.contains_aggregate:
            return [self]
        cols = []
        for source in self.get_source_expressions():
            cols.extend(source.get_group_by_cols())
        return cols