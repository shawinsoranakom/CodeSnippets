def csrf_trusted_origins_hosts(self):
        return [
            urlsplit(origin).netloc.lstrip("*")
            for origin in settings.CSRF_TRUSTED_ORIGINS
        ]