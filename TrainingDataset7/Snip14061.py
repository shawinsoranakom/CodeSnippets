def __getitem__(self, index):
        return (self.func, self.args, self.kwargs)[index]