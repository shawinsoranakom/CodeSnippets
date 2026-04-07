def test_deconstruct_type(self):
        """
        #22951 -- Uninstantiated classes with deconstruct are correctly
        returned by deep_deconstruct during serialization.
        """
        author = ModelState(
            "testapp",
            "Author",
            [
                ("id", models.AutoField(primary_key=True)),
                (
                    "name",
                    models.CharField(
                        max_length=200,
                        # IntegerField intentionally not instantiated.
                        default=models.IntegerField,
                    ),
                ),
            ],
        )
        changes = self.get_changes([], [author])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["CreateModel"])