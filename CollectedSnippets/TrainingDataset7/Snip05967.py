def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        rel_to = self.rel.model
        if self.admin_site.is_registered(rel_to):
            # The related object is registered with the same AdminSite
            related_url = reverse(
                "admin:%s_%s_changelist"
                % (
                    rel_to._meta.app_label,
                    rel_to._meta.model_name,
                ),
                current_app=self.admin_site.name,
            )

            params = self.url_parameters()
            if params:
                related_url += "?" + urlencode(params)
            context["related_url"] = related_url
            context["link_title"] = _("Lookup")
            # The JavaScript code looks for this class.
            css_class = "vForeignKeyRawIdAdminField"
            if isinstance(self.rel.get_related_field(), UUIDField):
                css_class += " vUUIDField"
            context["widget"]["attrs"].setdefault("class", css_class)
        else:
            context["related_url"] = None
        if context["widget"]["value"]:
            context["link_label"], context["link_url"] = self.label_and_url_for_value(
                value
            )
        else:
            context["link_label"] = None
        return context