def i18n_javascript(self, request, extra_context=None):
        """
        Display the i18n JavaScript that the Django admin requires.

        `extra_context` is unused but present for consistency with the other
        admin views.
        """
        return JavaScriptCatalog.as_view(packages=["django.contrib.admin"])(request)