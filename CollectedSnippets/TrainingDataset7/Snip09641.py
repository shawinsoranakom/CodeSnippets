def var(self, *args):
        return VariableWrapper(self.cursor.var(*args))