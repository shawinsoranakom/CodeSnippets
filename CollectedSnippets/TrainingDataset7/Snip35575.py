def test_rollback(self):
        with self.assertRaisesMessage(Exception, "Oops"):
            with transaction.atomic():
                Reporter.objects.create(first_name="Haddock")
                raise Exception("Oops, that's his last name")
        self.assertSequenceEqual(Reporter.objects.all(), [])