def resolve_expression(self, *args, **kwargs):
        if isinstance(self.name, self.__class__):
            return self.name
        return ResolvedOuterRef(self.name)