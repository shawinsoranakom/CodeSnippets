def related_model(self):
        # Can't cache this property until all the models are loaded.
        apps.check_models_ready()
        return self.remote_field.model