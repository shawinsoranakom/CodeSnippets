def test_bulk_insert_expressions(self):
        Restaurant.objects.bulk_create(
            [
                Restaurant(name="Sam's Shake Shack"),
                Restaurant(name=Lower(Value("Betty's Beetroot Bar"))),
            ]
        )
        bbb = Restaurant.objects.filter(name="betty's beetroot bar")
        self.assertEqual(bbb.count(), 1)