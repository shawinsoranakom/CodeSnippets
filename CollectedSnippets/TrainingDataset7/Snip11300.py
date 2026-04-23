def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # Attach update_dimension_fields so that dimension fields declared
        # after their corresponding image field don't stay cleared by
        # Model.__init__, see bug #11196.
        # Only run post-initialization dimension update on non-abstract models
        # with width_field/height_field.
        if not cls._meta.abstract and (self.width_field or self.height_field):
            signals.post_init.connect(self.update_dimension_fields, sender=cls)