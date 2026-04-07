def _add_script_prefix(value):
        """
        Add SCRIPT_NAME prefix to relative paths.

        Useful when the app is being served at a subpath and manually prefixing
        subpath to STATIC_URL and MEDIA_URL in settings is inconvenient.
        """
        # Don't apply prefix to absolute paths and URLs.
        if value.startswith(("http://", "https://", "/")):
            return value
        from django.urls import get_script_prefix

        return "%s%s" % (get_script_prefix(), value)