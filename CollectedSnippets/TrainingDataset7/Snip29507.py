def test_string_agg_delimiter_deprecation(self):
        msg = (
            "delimiter: str will be resolved as a field reference instead "
            'of a string literal on Django 7.0. Pass `delimiter=Value("\'")` to '
            "preserve the previous behavior."
        )

        with self.assertWarnsMessage(RemovedInDjango70Warning, msg) as ctx:
            values = AggregateTestModel.objects.aggregate(
                stringagg=StringAgg("char_field", delimiter="'")
            )
            self.assertEqual(values, {"stringagg": "Foo1'Foo2'Foo4'Foo3"})
        self.assertEqual(ctx.filename, __file__)