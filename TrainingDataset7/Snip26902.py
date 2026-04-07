def test_swappable_many_to_many_model_case(self):
        document_lowercase = ModelState(
            "testapp",
            "Document",
            [
                ("id", models.AutoField(primary_key=True)),
                ("owners", models.ManyToManyField(settings.AUTH_USER_MODEL.lower())),
            ],
        )
        document = ModelState(
            "testapp",
            "Document",
            [
                ("id", models.AutoField(primary_key=True)),
                ("owners", models.ManyToManyField(settings.AUTH_USER_MODEL)),
            ],
        )
        with isolate_lru_cache(apps.get_swappable_settings_name):
            changes = self.get_changes(
                [self.custom_user, document_lowercase],
                [self.custom_user, document],
            )
        self.assertEqual(len(changes), 0)