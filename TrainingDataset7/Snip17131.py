def test_aggregate_duplicate_columns_only(self):
        # Works with only() too.
        results = Author.objects.only("id", "name").annotate(
            num_contacts=Count("book_contact_set")
        )
        _, _, grouping = results.query.get_compiler(using="default").pre_sql_setup()
        self.assertEqual(len(grouping), 1)
        self.assertIn("id", grouping[0][0])
        self.assertNotIn("name", grouping[0][0])
        self.assertNotIn("age", grouping[0][0])
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