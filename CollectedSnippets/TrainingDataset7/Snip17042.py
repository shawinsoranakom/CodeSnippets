def test_string_agg_requires_delimiter(self):
        with self.assertRaises(TypeError):
            Book.objects.aggregate(stringagg=StringAgg("name"))