def __len__(self):
        "Return the number of dimensions for this Point (either 0, 2 or 3)."
        if self.empty:
            return 0
        if self.hasz:
            return 3
        else:
            return 2