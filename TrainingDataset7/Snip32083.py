def test_get_namespace_default_imports(self):
        namespace = shell.Command().get_namespace()

        self.assertEqual(
            namespace,
            {
                "settings": settings,
                "connection": connection,
                "reset_queries": reset_queries,
                "models": models,
                "functions": functions,
                "timezone": timezone,
            },
        )