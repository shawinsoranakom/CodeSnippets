def ct_field_attname(self):
        return self.model._meta.get_field(self.ct_field).attname