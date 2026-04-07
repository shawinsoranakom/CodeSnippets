def __eq__(self, other):
        return self.val == other or round(abs(self.val - other), self.places) == 0