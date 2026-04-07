def test_stringagg_default_value(self):
        result = Author.objects.filter(age__gt=100).aggregate(
            value=StringAgg("name", delimiter=Value(";"), default=Value("<empty>")),
        )
        self.assertEqual(result["value"], "<empty>")