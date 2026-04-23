def __repr__(self):
        out = [str(x) for x in [self.id, self.first, self.second] if x is not None]
        return "(" + " ".join(out) + ")"