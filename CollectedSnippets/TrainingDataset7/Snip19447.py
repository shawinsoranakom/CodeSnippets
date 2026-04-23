def get_settings(self, module_name, module_path, name="django"):
        return {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "NAME": name,
            "OPTIONS": {
                "libraries": {
                    module_name: f"check_framework.template_test_apps.{module_path}",
                },
            },
        }