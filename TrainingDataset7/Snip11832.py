def __str__(self):
        """Return "app_label.model_label.manager_name"."""
        return "%s.%s" % (self.model._meta.label, self.name)