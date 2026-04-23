def test_connection(self):
        instance = CashModel.objects.get()
        self.assertEqual(instance.cash.vendor, connection.vendor)