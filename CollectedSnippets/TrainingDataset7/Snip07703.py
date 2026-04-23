def model(self):
        try:
            return self.__dict__["model"]
        except KeyError:
            raise AttributeError(
                "'%s' object has no attribute 'model'" % self.__class__.__name__
            )