def get_template_names(self):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if render_to_response is overridden.
        """
        try:
            names = super().get_template_names()
        except ImproperlyConfigured:
            # If template_name isn't specified, it's not a problem --
            # we just start with an empty list.
            names = []

        # If the list is a queryset, we'll invent a template name based on the
        # app and model name. This name gets put at the end of the template
        # name list so that user-supplied names override the automatically-
        # generated ones.
        if hasattr(self.object_list, "model"):
            opts = self.object_list.model._meta
            names.append(
                "%s/%s%s.html"
                % (opts.app_label, opts.model_name, self.template_name_suffix)
            )
        elif not names:
            raise ImproperlyConfigured(
                "%(cls)s requires either a 'template_name' attribute "
                "or a get_queryset() method that returns a QuerySet."
                % {
                    "cls": self.__class__.__name__,
                }
            )
        return names