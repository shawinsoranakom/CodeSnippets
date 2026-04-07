def test_m2m_target_change_generates_remove_and_add(self):
        before = [
            self.publisher,
            self.other_publisher,
            self.author_with_m2m,  # m2m to self.publisher.
        ]

        after = [
            self.publisher,
            self.other_publisher,
            ModelState(
                "testapp",
                "Author",
                [
                    ("id", models.AutoField(primary_key=True)),
                    # Repoint m2m to self.other_publisher.
                    ("publishers", models.ManyToManyField("testapp.OtherPublisher")),
                ],
            ),
        ]
        changes = self.get_changes(before, after)
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["RemoveField", "AddField"])
        self.assertOperationAttributes(
            changes,
            "testapp",
            0,
            0,
            name="publishers",
            model_name="author",
        )
        self.assertOperationAttributes(
            changes,
            "testapp",
            0,
            1,
            name="publishers",
            model_name="author",
        )