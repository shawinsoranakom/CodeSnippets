def test_swappable_first_setting(self):
        """Swappable models get their CreateModel first."""
        with isolate_lru_cache(apps.get_swappable_settings_name):
            changes = self.get_changes([], [self.custom_user_no_inherit, self.aardvark])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "thirdapp", 1)
        self.assertOperationTypes(
            changes, "thirdapp", 0, ["CreateModel", "CreateModel"]
        )
        self.assertOperationAttributes(changes, "thirdapp", 0, 0, name="CustomUser")
        self.assertOperationAttributes(changes, "thirdapp", 0, 1, name="Aardvark")