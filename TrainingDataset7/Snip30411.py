def test_insert_returning_non_integer(self):
        obj = NonIntegerPKReturningModel.objects.create()
        self.assertTrue(obj.created)
        self.assertIsInstance(obj.created, datetime.datetime)