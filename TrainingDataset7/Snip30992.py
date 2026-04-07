def test_decimal_parameter(self):
        c = Coffee.objects.create(brand="starbucks", price=20.5)
        qs = Coffee.objects.raw(
            "SELECT * FROM raw_query_coffee WHERE price >= %s", params=[Decimal(20)]
        )
        self.assertEqual(list(qs), [c])