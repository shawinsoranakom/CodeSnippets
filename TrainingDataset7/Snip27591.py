def test_choices_iterator(self):
        """
        #24483 - ProjectState.from_apps should not destructively consume
        Field.choices iterators.
        """
        new_apps = Apps(["migrations"])
        choices = [("a", "A"), ("b", "B")]

        class Author(models.Model):
            name = models.CharField(max_length=255)
            choice = models.CharField(max_length=255, choices=iter(choices))

            class Meta:
                app_label = "migrations"
                apps = new_apps

        ProjectState.from_apps(new_apps)
        choices_field = Author._meta.get_field("choice")
        self.assertEqual(list(choices_field.choices), choices)