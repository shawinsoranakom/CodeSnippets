def test_commit(self):
        with transaction.atomic(durable=True):
            reporter = Reporter.objects.create(first_name="Tintin")
        self.assertEqual(Reporter.objects.get(), reporter)