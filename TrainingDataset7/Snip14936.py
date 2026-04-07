def get_template_names(self):
        """
        Return a list of template names to be used for the request. May not be
        called if render_to_response() is overridden. Return a list containing
        ``template_name``, if set on the value. Otherwise, return a list
        containing:

        * the contents of the ``template_name_field`` field on the
          object instance that the view is operating upon (if available)
        * ``<app_label>/<model_name><template_name_suffix>.html``
        """
        try:
            names = super().get_template_names()
        except ImproperlyConfigured:
            # If template_name isn't specified, it's not a problem --
            # we just start with an empty list.
            names = []

            # If self.template_name_field is set, grab the value of the field
            # of that name from the object; this is the most specific template
            # name, if given.
            if self.object and self.template_name_field:
                name = getattr(self.object, self.template_name_field, None)
                if name:
                    names.insert(0, name)

            # The least-specific option is the default
            # <app>/<model>_detail.html; only use this if the object in
            # question is a model.
            if isinstance(self.object, models.Model):
                object_meta = self.object._meta
                names.append(
                    "%s/%s%s.html"
                    % (
                        object_meta.app_label,
                        object_meta.model_name,
                        self.template_name_suffix,
                    )
                )
            elif getattr(self, "model", None) is not None and issubclass(
                self.model, models.Model
            ):
                names.append(
                    "%s/%s%s.html"
                    % (
                        self.model._meta.app_label,
                        self.model._meta.model_name,
                        self.template_name_suffix,
                    )
                )

            # If we still haven't managed to find any template names, we should
            # re-raise the ImproperlyConfigured to alert the user.
            if not names:
                raise ImproperlyConfigured(
                    "SingleObjectTemplateResponseMixin requires a definition "
                    "of 'template_name', 'template_name_field', or 'model'; "
                    "or an implementation of 'get_template_names()'."
                )

        return names