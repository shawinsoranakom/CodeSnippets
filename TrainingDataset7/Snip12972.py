def tell(self):
        raise OSError(
            "This %s instance cannot tell its position" % self.__class__.__name__
        )