def pre_save(self, model_instance, add):
        """Return field's value just before saving."""
        return getattr(model_instance, self.attname)