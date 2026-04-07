def __setattr__(self, key, value):
        if key == "var":
            self.__dict__[key] = value
        else:
            setattr(self.var, key, value)