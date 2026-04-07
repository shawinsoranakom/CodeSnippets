def contribute_to_class(self, cls, name, private_only=False):
        super().contribute_to_class(cls, name, private_only)
        setattr(cls, self.name, ReverseManyToOneDescriptor(self))