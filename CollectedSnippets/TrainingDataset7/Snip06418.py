def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, private_only=True, **kwargs)
        setattr(cls, self.attname, GenericForeignKeyDescriptor(self))