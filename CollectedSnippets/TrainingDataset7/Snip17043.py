def test_string_agg_escapes_delimiter(self):
        values = Publisher.objects.aggregate(
            stringagg=StringAgg("name", delimiter=Value("'"))
        )

        self.assertEqual(
            values,
            {
                "stringagg": "Apress'Sams'Prentice Hall'Morgan Kaufmann'Jonno's House "
                "of Books",
            },
        )