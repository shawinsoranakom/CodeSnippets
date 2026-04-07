def arrayvar(self, *args):
        return VariableWrapper(self.cursor.arrayvar(*args))