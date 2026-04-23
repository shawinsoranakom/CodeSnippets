def get_lhs_str(self):
        if isinstance(self.lhs, ColPairs):
            return repr(self.lhs.field.name)
        else:
            names = ", ".join(repr(f.name) for f in self.lhs)
            return f"({names})"