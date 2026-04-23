def test_one_to_one(self):
        # Test basic pointing
        from django.contrib.auth.models import Permission

        field = models.OneToOneField("auth.Permission", models.CASCADE)
        field.remote_field.model = Permission
        field.remote_field.field_name = "id"
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.OneToOneField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"to": "auth.permission", "on_delete": models.CASCADE})
        self.assertFalse(hasattr(kwargs["to"], "setting_name"))
        # Test swap detection for swappable model
        field = models.OneToOneField("auth.User", models.CASCADE)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.OneToOneField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"to": "auth.user", "on_delete": models.CASCADE})
        self.assertEqual(kwargs["to"].setting_name, "AUTH_USER_MODEL")
        # Test nonexistent (for now) model
        field = models.OneToOneField("something.Else", models.CASCADE)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.OneToOneField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"to": "something.else", "on_delete": models.CASCADE})
        # Test on_delete
        field = models.OneToOneField("auth.User", models.SET_NULL)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.OneToOneField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"to": "auth.user", "on_delete": models.SET_NULL})
        # Test to_field
        field = models.OneToOneField(
            "auth.Permission", models.CASCADE, to_field="foobar"
        )
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.OneToOneField")
        self.assertEqual(args, [])
        self.assertEqual(
            kwargs,
            {
                "to": "auth.permission",
                "to_field": "foobar",
                "on_delete": models.CASCADE,
            },
        )
        # Test related_name
        field = models.OneToOneField(
            "auth.Permission", models.CASCADE, related_name="foobar"
        )
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.OneToOneField")
        self.assertEqual(args, [])
        self.assertEqual(
            kwargs,
            {
                "to": "auth.permission",
                "related_name": "foobar",
                "on_delete": models.CASCADE,
            },
        )
        # Test related_query_name
        field = models.OneToOneField(
            "auth.Permission", models.CASCADE, related_query_name="foobar"
        )
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.OneToOneField")
        self.assertEqual(args, [])
        self.assertEqual(
            kwargs,
            {
                "to": "auth.permission",
                "related_query_name": "foobar",
                "on_delete": models.CASCADE,
            },
        )
        # Test limit_choices_to
        field = models.OneToOneField(
            "auth.Permission", models.CASCADE, limit_choices_to={"foo": "bar"}
        )
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.OneToOneField")
        self.assertEqual(args, [])
        self.assertEqual(
            kwargs,
            {
                "to": "auth.permission",
                "limit_choices_to": {"foo": "bar"},
                "on_delete": models.CASCADE,
            },
        )
        # Test unique
        field = models.OneToOneField("auth.Permission", models.CASCADE, unique=True)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.OneToOneField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"to": "auth.permission", "on_delete": models.CASCADE})