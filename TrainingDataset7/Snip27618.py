def test_create_swappable(self):
        """
        Tests making a ProjectState from an Apps with a swappable model
        """
        new_apps = Apps(["migrations"])

        class Author(models.Model):
            name = models.CharField(max_length=255)
            bio = models.TextField()
            age = models.IntegerField(blank=True, null=True)

            class Meta:
                app_label = "migrations"
                apps = new_apps
                swappable = "TEST_SWAPPABLE_MODEL"

        author_state = ModelState.from_model(Author)
        self.assertEqual(author_state.app_label, "migrations")
        self.assertEqual(author_state.name, "Author")
        self.assertEqual(list(author_state.fields), ["id", "name", "bio", "age"])
        self.assertEqual(author_state.fields["name"].max_length, 255)
        self.assertIs(author_state.fields["bio"].null, False)
        self.assertIs(author_state.fields["age"].null, True)
        self.assertEqual(
            author_state.options,
            {"swappable": "TEST_SWAPPABLE_MODEL", "indexes": [], "constraints": []},
        )
        self.assertEqual(author_state.bases, (models.Model,))
        self.assertEqual(author_state.managers, [])