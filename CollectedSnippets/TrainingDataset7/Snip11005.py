def __str__(self):
        """
        Return "app_label.model_label.field_name" for fields attached to
        models.
        """
        if not hasattr(self, "model"):
            return super().__str__()
        model = self.model
        return "%s.%s" % (model._meta.label, self.name)