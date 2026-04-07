def test_merged_rollback_rollback(self):
        with self.assertRaisesMessage(Exception, "Oops"):
            with transaction.atomic():
                Reporter.objects.create(last_name="Tintin")
                with self.assertRaisesMessage(Exception, "Oops"):
                    with transaction.atomic(savepoint=False):
                        Reporter.objects.create(first_name="Haddock")
                    raise Exception("Oops, that's his last name")
                raise Exception("Oops, that's his first name")
        self.assertSequenceEqual(Reporter.objects.all(), [])