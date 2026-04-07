def allowed_origins_exact(self):
        return {origin for origin in settings.CSRF_TRUSTED_ORIGINS if "*" not in origin}