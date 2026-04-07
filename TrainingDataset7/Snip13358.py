def render(self, context):
        csrf_token = context.get("csrf_token")
        if csrf_token:
            if csrf_token == "NOTPROVIDED":
                return format_html("")
            else:
                return format_html(
                    '<input type="hidden" name="csrfmiddlewaretoken" value="{}">',
                    csrf_token,
                )
        else:
            # It's very probable that the token is missing because of
            # misconfiguration, so we raise a warning
            if settings.DEBUG:
                warnings.warn(
                    "A {% csrf_token %} was used in a template, but the context "
                    "did not provide the value. This is usually caused by not "
                    "using RequestContext."
                )
            return ""