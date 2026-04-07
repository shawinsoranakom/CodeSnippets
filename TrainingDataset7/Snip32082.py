def test_get_namespace(self):
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
                "Marker": Marker,
                "Phone": Phone,
                "ContentType": ContentType,
                "Group": Group,
                "Permission": Permission,
                "User": User,
            },
        )