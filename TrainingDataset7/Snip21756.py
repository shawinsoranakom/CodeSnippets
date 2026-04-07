def test_many_to_many_field(self):
        # Test normal
        field = models.ManyToManyField("auth.Permission")
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.ManyToManyField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"to": "auth.permission"})
        self.assertFalse(hasattr(kwargs["to"], "setting_name"))
        # Test swappable
        field = models.ManyToManyField("auth.User")
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.ManyToManyField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"to": "auth.user"})
        self.assertEqual(kwargs["to"].setting_name, "AUTH_USER_MODEL")
        # Test through
        field = models.ManyToManyField("auth.Permission", through="auth.Group")
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.ManyToManyField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"to": "auth.permission", "through": "auth.Group"})
        # Test through_fields
        field = models.ManyToManyField(
            "auth.Permission",
            through="auth.Group",
            through_fields=("foo", "permissions"),
        )
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.ManyToManyField")
        self.assertEqual(args, [])
        self.assertEqual(
            kwargs,
            {
                "to": "auth.permission",
                "through": "auth.Group",
                "through_fields": ("foo", "permissions"),
            },
        )
        # Test custom db_table
        field = models.ManyToManyField("auth.Permission", db_table="custom_table")
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.ManyToManyField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"to": "auth.permission", "db_table": "custom_table"})
        # Test related_name
        field = models.ManyToManyField("auth.Permission", related_name="custom_table")
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.ManyToManyField")
        self.assertEqual(args, [])
        self.assertEqual(
            kwargs, {"to": "auth.permission", "related_name": "custom_table"}
        )
        # Test related_query_name
        field = models.ManyToManyField("auth.Permission", related_query_name="foobar")
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.ManyToManyField")
        self.assertEqual(args, [])
        self.assertEqual(
            kwargs, {"to": "auth.permission", "related_query_name": "foobar"}
        )
        # Test limit_choices_to
        field = models.ManyToManyField(
            "auth.Permission", limit_choices_to={"foo": "bar"}
        )
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.ManyToManyField")
        self.assertEqual(args, [])
        self.assertEqual(
            kwargs, {"to": "auth.permission", "limit_choices_to": {"foo": "bar"}}
        )