def get_auto_imports(self):
                # Include duplicate import strings to ensure proper handling,
                # independent of isort's deduplication (#36252).
                return super().get_auto_imports() + [
                    "django.urls.reverse",
                    "django.urls.resolve",
                    "shell",
                    "django",
                    "django.urls.reverse",
                    "shell",
                    "django",
                ]