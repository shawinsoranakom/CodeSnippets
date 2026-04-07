def test_combine_join_reuse(self):
        # Joins having identical connections are correctly recreated in the
        # rhs query, in case the query is ORed together (#18748).
        Report.objects.create(name="r4", creator=self.a1)
        q1 = Author.objects.filter(report__name="r5")
        q2 = Author.objects.filter(report__name="r4").filter(report__name="r1")
        combined = q1 | q2
        self.assertEqual(str(combined.query).count("JOIN"), 2)
        self.assertEqual(len(combined), 1)
        self.assertEqual(combined[0].name, "a1")