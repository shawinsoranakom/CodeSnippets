def name(self):
        model = self.model_class()
        if not model:
            return self.model
        return str(model._meta.verbose_name)