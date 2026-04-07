def __deepcopy__(self, memo):
        obj = super().__deepcopy__(memo)
        obj.widgets = copy.deepcopy(self.widgets)
        return obj