def get_context(self, name, value, attrs):
        try:
            self.validator(value if value else "")
            url_valid = True
        except ValidationError:
            url_valid = False
        context = super().get_context(name, value, attrs)
        context["current_label"] = _("Currently:")
        context["change_label"] = _("Change:")
        context["widget"]["href"] = (
            smart_urlquote(context["widget"]["value"]) if url_valid else ""
        )
        context["url_valid"] = url_valid
        return context