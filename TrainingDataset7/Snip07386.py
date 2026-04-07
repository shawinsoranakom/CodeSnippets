def sort(self, key=None, reverse=False):
        "Standard list sort method"
        self[:] = sorted(self, key=key, reverse=reverse)