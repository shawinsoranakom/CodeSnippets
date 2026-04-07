def __set__(self, instance, value):
        ct = None
        fk = None
        if value is not None:
            ct = self.field.get_content_type(obj=value)
            fk = value.pk

        setattr(instance, self.field.ct_field, ct)
        setattr(instance, self.field.fk_field, fk)
        self.field.set_cached_value(instance, value)