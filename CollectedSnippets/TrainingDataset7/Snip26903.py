def test_swappable_changed(self):
        with isolate_lru_cache(apps.get_swappable_settings_name):
            before = self.make_project_state([self.custom_user, self.author_with_user])
            with override_settings(AUTH_USER_MODEL="thirdapp.CustomUser"):
                after = self.make_project_state(
                    [self.custom_user, self.author_with_custom_user]
                )
            autodetector = MigrationAutodetector(before, after)
            changes = autodetector._detect_changes()
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AlterField"])
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, model_name="author", name="user"
        )
        fk_field = changes["testapp"][0].operations[0].field
        self.assertEqual(fk_field.remote_field.model, "thirdapp.CustomUser")