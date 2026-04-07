def test_aggregate_duplicate_columns(self):
        # Regression test for #17144

        results = Author.objects.annotate(num_contacts=Count("book_contact_set"))

        # There should only be one GROUP BY clause, for the `id` column.
        # `name` and `age` should not be grouped on.
        _, _, group_by = results.query.get_compiler(using="default").pre_sql_setup()
        self.assertEqual(len(group_by), 1)
        self.assertIn("id", group_by[0][0])
        self.assertNotIn("name", group_by[0][0])
        self.assertNotIn("age", group_by[0][0])
        self.assertEqual(
            [(a.name, a.num_contacts) for a in results.order_by("name")],
            [
                ("Adrian Holovaty", 1),
                ("Brad Dayley", 1),
                ("Jacob Kaplan-Moss", 0),
                ("James Bennett", 1),
                ("Jeffrey Forcier", 1),
                ("Paul Bissex", 0),
                ("Peter Norvig", 2),
                ("Stuart Russell", 0),
                ("Wesley J. Chun", 0),
            ],
        )