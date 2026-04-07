def get_settings(setting, cache_path, setting_path):
        return {
            "CACHES": {
                "default": {
                    "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
                    "LOCATION": cache_path,
                },
            },
            setting: [setting_path] if setting == "STATICFILES_DIRS" else setting_path,
        }