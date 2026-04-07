def clean_url(self):
        url = self.cleaned_data["url"]
        if not url.startswith("/"):
            raise ValidationError(
                gettext("URL is missing a leading slash."),
                code="missing_leading_slash",
            )
        if self._trailing_slash_required() and not url.endswith("/"):
            raise ValidationError(
                gettext("URL is missing a trailing slash."),
                code="missing_trailing_slash",
            )
        return url