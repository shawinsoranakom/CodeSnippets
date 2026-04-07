def test_insert_returning_non_integer_from_literal_value(self):
        obj = NonIntegerPKReturningModel.objects.create(pk="2025-01-01")
        self.assertTrue(obj.created)
        self.assertIsInstance(obj.created, datetime.datetime)