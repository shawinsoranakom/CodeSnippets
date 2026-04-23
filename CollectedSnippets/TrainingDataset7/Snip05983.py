def get_context(self, name, value, attrs):
        from django.contrib.admin.views.main import (
            IS_POPUP_VAR,
            SOURCE_MODEL_VAR,
            TO_FIELD_VAR,
        )

        rel_opts = self.rel.model._meta
        info = (rel_opts.app_label, rel_opts.model_name)
        related_field_name = self.rel.get_related_field().name
        app_label = self.rel.field.model._meta.app_label
        model_name = self.rel.field.model._meta.model_name

        url_params = "&".join(
            "%s=%s" % param
            for param in [
                (TO_FIELD_VAR, related_field_name),
                (IS_POPUP_VAR, 1),
                (SOURCE_MODEL_VAR, f"{app_label}.{model_name}"),
            ]
        )
        context = {
            "rendered_widget": self.widget.render(name, value, attrs),
            "is_hidden": self.is_hidden,
            "name": name,
            "url_params": url_params,
            "model": rel_opts.verbose_name,
            "model_name": rel_opts.model_name,
            "can_add_related": self.can_add_related,
            "can_change_related": self.can_change_related,
            "can_delete_related": self.can_delete_related,
            "can_view_related": self.can_view_related,
            "model_has_limit_choices_to": self.rel.limit_choices_to,
        }
        if self.can_add_related:
            context["add_related_url"] = self.get_related_url(info, "add")
        if self.can_delete_related:
            context["delete_related_template_url"] = self.get_related_url(
                info, "delete", "__fk__"
            )
        if self.can_view_related or self.can_change_related:
            context["view_related_url_params"] = f"{TO_FIELD_VAR}={related_field_name}"
            context["change_related_template_url"] = self.get_related_url(
                info, "change", "__fk__"
            )
        return context