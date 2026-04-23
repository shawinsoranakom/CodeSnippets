def test_add_constraints_with_dict_keys(self):
        book_types = {"F": "Fantasy", "M": "Mystery"}
        book_with_type = ModelState(
            "testapp",
            "Book",
            [
                ("id", models.AutoField(primary_key=True)),
                ("type", models.CharField(max_length=1)),
            ],
            {
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(type__in=book_types.keys()),
                        name="book_type_check",
                    ),
                ],
            },
        )
        book_with_resolved_type = ModelState(
            "testapp",
            "Book",
            [
                ("id", models.AutoField(primary_key=True)),
                ("type", models.CharField(max_length=1)),
            ],
            {
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("type__in", tuple(book_types))),
                        name="book_type_check",
                    ),
                ],
            },
        )
        changes = self.get_changes([book_with_type], [book_with_resolved_type])
        self.assertEqual(len(changes), 0)