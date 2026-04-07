def save(self, name, content, save=True):
        name = self.field.generate_filename(self.instance, name)
        self.name = self.storage.save(name, content, max_length=self.field.max_length)
        self._set_instance_attribute(self.name, content)
        self._committed = True

        # Save the object because it has changed, unless save is False
        if save:
            self.instance.save()