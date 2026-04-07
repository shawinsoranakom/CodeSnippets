def test_subquery_condition(self):
        qs1 = Tag.objects.filter(pk__lte=0)
        qs2 = Tag.objects.filter(parent__in=qs1)
        qs3 = Tag.objects.filter(parent__in=qs2)
        self.assertEqual(qs3.query.subq_aliases, {"T", "U", "V"})
        self.assertIn("v0", str(qs3.query).lower())
        qs4 = qs3.filter(parent__in=qs1)
        self.assertEqual(qs4.query.subq_aliases, {"T", "U", "V"})
        # It is possible to reuse U for the second subquery, no need to use W.
        self.assertNotIn("w0", str(qs4.query).lower())
        # So, 'U0."id"' is referenced in SELECT and WHERE twice.
        id_col = "%s." % connection.ops.quote_name("u0").lower()
        self.assertEqual(str(qs4.query).lower().count(id_col), 4)