def __str__(self):
        return ":".join(
            (
                self.__class__.__name__,
                self.name,
            )
        )