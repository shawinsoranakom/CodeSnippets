def _set_instance_attribute(self, name, content):
        setattr(self.instance, self.field.attname, name)