def setting_changed(self, *, setting, **kwargs):
        if setting == self.swappable and "swapped" in self.__dict__:
            del self.swapped