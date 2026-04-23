def test_sequence_of_durables(self):
        with transaction.atomic(durable=True):
            reporter = Reporter.objects.create(first_name="Tintin 1")
        self.assertEqual(Reporter.objects.get(first_name="Tintin 1"), reporter)
        with transaction.atomic(durable=True):
            reporter = Reporter.objects.create(first_name="Tintin 2")
        self.assertEqual(Reporter.objects.get(first_name="Tintin 2"), reporter)