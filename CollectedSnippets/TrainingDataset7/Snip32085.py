def test_get_namespace_overridden(self):
        class TestCommand(shell.Command):
            def get_auto_imports(self):
                return super().get_auto_imports() + [
                    "django.urls.reverse",
                    "django.urls.resolve",
                ]

        namespace = TestCommand().get_namespace()

        self.assertEqual(
            namespace,
            {
                "resolve": resolve,
                "reverse": reverse,
                "settings": settings,
                "connection": connection,
                "reset_queries": reset_queries,
                "models": models,
                "functions": functions,
                "timezone": timezone,
                "Marker": Marker,
                "Phone": Phone,
                "ContentType": ContentType,
                "Group": Group,
                "Permission": Permission,
                "User": User,
            },
        )