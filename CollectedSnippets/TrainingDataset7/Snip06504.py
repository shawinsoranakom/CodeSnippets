def app_labeled_name(self):
        model = self.model_class()
        if not model:
            return "%s | %s" % (self.app_label, self.model)
        return "%s | %s" % (
            model._meta.app_config.verbose_name,
            model._meta.verbose_name,
        )