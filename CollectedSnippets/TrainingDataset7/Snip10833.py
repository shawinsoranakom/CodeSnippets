def __getitem__(self, subscript):
        return Sliced(self, subscript)