def contribute_to_class(self, cls, name, private_only=False):
        super().contribute_to_class(cls, name, private_only=private_only)
        cls._meta.pk = self
        setattr(cls, self.attname, self.descriptor_class(self))