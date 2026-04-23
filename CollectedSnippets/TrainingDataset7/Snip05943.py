def __repr__(self):
        return "<%s: model=%s model_admin=%s>" % (
            self.__class__.__qualname__,
            self.model.__qualname__,
            self.model_admin.__class__.__qualname__,
        )