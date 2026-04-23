def copy(self):
        copy = super().copy()
        copy.error_class = self.error_class
        copy.renderer = self.renderer
        return copy