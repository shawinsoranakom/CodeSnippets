def text(self):
        raise AttributeError(
            "This %s instance has no `text` attribute." % self.__class__.__name__
        )