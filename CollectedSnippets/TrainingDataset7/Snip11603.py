def __repr__(self):
        return "<%s: %s.%s>" % (
            type(self).__name__,
            self.related_model._meta.app_label,
            self.related_model._meta.model_name,
        )