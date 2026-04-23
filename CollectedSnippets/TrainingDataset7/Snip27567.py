def test_no_duplicate_managers(self):
        """
        When a manager is added with `use_in_migrations = True` and a parent
        model had a manager with the same name and `use_in_migrations = True`,
        the parent's manager shouldn't appear in the model state (#26881).
        """
        new_apps = Apps(["migrations"])

        class PersonManager(models.Manager):
            use_in_migrations = True

        class Person(models.Model):
            objects = PersonManager()

            class Meta:
                abstract = True

        class BossManager(PersonManager):
            use_in_migrations = True

        class Boss(Person):
            objects = BossManager()

            class Meta:
                app_label = "migrations"
                apps = new_apps

        project_state = ProjectState.from_apps(new_apps)
        boss_state = project_state.models["migrations", "boss"]
        self.assertEqual(boss_state.managers, [("objects", Boss.objects)])