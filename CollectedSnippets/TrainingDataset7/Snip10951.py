def copy(self):
        clone = super().copy()
        clone.query = clone.query.clone()
        return clone