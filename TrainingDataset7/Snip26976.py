def test_auto(self):
        migration = migrations.Migration("0001_initial", "test_app")
        suggest_name = migration.suggest_name()
        self.assertIs(suggest_name.startswith("auto_"), True)