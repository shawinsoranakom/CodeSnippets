def _set_instance_attribute(self, name, content):
        setattr(self.instance, self.field.attname, content)
        # Update the name in case generate_filename() or storage.save() changed
        # it, but bypass the descriptor to avoid re-reading the file.
        self.instance.__dict__[self.field.attname] = self.name