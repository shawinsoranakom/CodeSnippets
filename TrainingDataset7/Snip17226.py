def test_alias_forbidden_chars(self):
        tests = [
            'al"ias',
            "a'lias",
            "ali`as",
            "alia s",
            "alias\t",
            "ali\nas",
            "alias--",
            "ali/*as",
            "alias*/",
            "alias;",
            # RemovedInDjango70Warning: When the deprecation ends, add this:
            # "alias%",
            # [] and # are used by MSSQL.
            "alias[",
            "alias]",
            "ali#as",
            "ali\0as",
        ]
        # RemovedInDjango70Warning: When the deprecation ends, replace with:
        # msg = (
        #    "Column aliases cannot contain whitespace characters, hashes, "
        #    "quotation marks, semicolons, percent signs, or SQL comments."
        # )
        msg = (
            "Column aliases cannot contain whitespace characters, hashes, "
            "control characters, quotation marks, semicolons, or SQL comments."
        )
        for crafted_alias in tests:
            with self.subTest(crafted_alias):
                with self.assertRaisesMessage(ValueError, msg):
                    Book.objects.annotate(**{crafted_alias: Value(1)})

                with self.assertRaisesMessage(ValueError, msg):
                    Book.objects.annotate(
                        **{crafted_alias: FilteredRelation("authors")}
                    )