def test_string_agg_deprecation(self):
        msg = (
            "The PostgreSQL specific StringAgg function is deprecated. Use "
            "django.db.models.aggregates.StringAgg instead."
        )

        with self.assertWarnsMessage(RemovedInDjango70Warning, msg) as ctx:
            values = AggregateTestModel.objects.aggregate(
                stringagg=StringAgg("char_field", delimiter=Value("'"))
            )
            self.assertEqual(values, {"stringagg": "Foo1'Foo2'Foo4'Foo3"})
        self.assertEqual(ctx.filename, __file__)