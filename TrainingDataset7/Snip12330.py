def get_group_by_cols(self):
        cols = []
        for child in self.children:
            cols.extend(child.get_group_by_cols())
        return cols