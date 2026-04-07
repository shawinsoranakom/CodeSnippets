def handle_simple(cls, path):
        if apps.is_installed("django.contrib.staticfiles"):
            from django.contrib.staticfiles.storage import staticfiles_storage

            return staticfiles_storage.url(path)
        else:
            return urljoin(PrefixNode.handle_simple("STATIC_URL"), quote(path))