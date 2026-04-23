def add_select_col(self, col, name):
        self.select += (col,)
        self.values_select += (name,)
        self.selected[name] = len(self.select) - 1