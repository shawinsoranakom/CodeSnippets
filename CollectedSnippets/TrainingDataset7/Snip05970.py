def label_and_url_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.model._default_manager.using(self.db).get(**{key: value})
        except (ValueError, self.rel.model.DoesNotExist, ValidationError):
            return "", ""

        try:
            url = reverse(
                "%s:%s_%s_change"
                % (
                    self.admin_site.name,
                    obj._meta.app_label,
                    obj._meta.model_name,
                ),
                args=(obj.pk,),
            )
        except NoReverseMatch:
            url = ""  # Admin not registered for target model.

        return Truncator(obj).words(14), url