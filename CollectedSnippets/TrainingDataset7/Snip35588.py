def test_force_rollback(self):
        with transaction.atomic():
            Reporter.objects.create(first_name="Tintin")
            # atomic block shouldn't rollback, but force it.
            self.assertFalse(transaction.get_rollback())
            transaction.set_rollback(True)
        self.assertSequenceEqual(Reporter.objects.all(), [])