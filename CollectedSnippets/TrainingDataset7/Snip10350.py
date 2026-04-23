def deconstruct(self):
        kwargs = {
            "model_name": self.model_name,
            "name": self.name,
        }
        return (
            self.__class__.__qualname__,
            [],
            kwargs,
        )