def test_swappable_circular_multi_mti(self):
        with isolate_lru_cache(apps.get_swappable_settings_name):
            parent = ModelState(
                "a",
                "Parent",
                [("user", models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE))],
            )
            child = ModelState("a", "Child", [], bases=("a.Parent",))
            user = ModelState("a", "User", [], bases=(AbstractBaseUser, "a.Child"))
            changes = self.get_changes([], [parent, child, user])
        self.assertNumberMigrations(changes, "a", 1)
        self.assertOperationTypes(
            changes, "a", 0, ["CreateModel", "CreateModel", "CreateModel", "AddField"]
        )