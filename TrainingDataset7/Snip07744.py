def __deepcopy__(self, memo):
        obj = super().__deepcopy__(memo)
        obj.widget = copy.deepcopy(self.widget)
        return obj