def setdefault(self, key, value):
        if key not in self:
            self[key] = value