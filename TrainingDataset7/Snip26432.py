def setUpClass(cls):
        cls.enterClassContext(
            override_settings(
                TEMPLATES=[
                    {
                        "BACKEND": "django.template.backends.django.DjangoTemplates",
                        "DIRS": [],
                        "APP_DIRS": True,
                        "OPTIONS": {
                            "context_processors": (
                                "django.contrib.auth.context_processors.auth",
                                "django.contrib.messages.context_processors.messages",
                            ),
                        },
                    }
                ],
                ROOT_URLCONF="messages_tests.urls",
                MESSAGE_TAGS={},
                MESSAGE_STORAGE=(
                    f"{cls.storage_class.__module__}.{cls.storage_class.__name__}"
                ),
                SESSION_SERIALIZER="django.contrib.sessions.serializers.JSONSerializer",
            )
        )
        super().setUpClass()