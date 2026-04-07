def test_check(self):
        class Author(Model):
            name = CharField(max_length=255)
            alias = CharField(max_length=255)

            class Meta:
                app_label = "postgres_tests"

        class Book(Model):
            title = CharField(max_length=255)
            published_date = DateField()
            author = ForeignKey(Author, CASCADE)

            class Meta:
                app_label = "postgres_tests"
                constraints = [
                    ExclusionConstraint(
                        name="exclude_check",
                        expressions=[
                            (F("title"), RangeOperators.EQUAL),
                            (F("published_date__year"), RangeOperators.EQUAL),
                            ("published_date__month", RangeOperators.EQUAL),
                            (F("author__name"), RangeOperators.EQUAL),
                            ("author__alias", RangeOperators.EQUAL),
                            ("nonexistent", RangeOperators.EQUAL),
                        ],
                    )
                ]

        self.assertCountEqual(
            Book.check(databases=self.databases),
            [
                Error(
                    "'constraints' refers to the nonexistent field 'nonexistent'.",
                    obj=Book,
                    id="models.E012",
                ),
                Error(
                    "'constraints' refers to the joined field 'author__alias'.",
                    obj=Book,
                    id="models.E041",
                ),
                Error(
                    "'constraints' refers to the joined field 'author__name'.",
                    obj=Book,
                    id="models.E041",
                ),
            ],
        )