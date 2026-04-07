def get_group_by_cols(self):
        if not self.cases:
            return self.default.get_group_by_cols()
        return super().get_group_by_cols()