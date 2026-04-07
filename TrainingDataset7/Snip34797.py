def test_15368(self):
        # Need to insert a context processor that assumes certain things about
        # the request instance. This triggers a bug caused by some ways of
        # copying RequestContext.
        with self.settings(
            TEMPLATES=[
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "APP_DIRS": True,
                    "OPTIONS": {
                        "context_processors": [
                            "test_client_regress.context_processors.special",
                        ],
                    },
                }
            ]
        ):
            response = self.client.get("/request_context_view/")
            self.assertContains(response, "Path: /request_context_view/")