def test_reuse_rollback_rollback(self):
        atomic = transaction.atomic()
        with self.assertRaisesMessage(Exception, "Oops"):
            with atomic:
                Reporter.objects.create(last_name="Tintin")
                with self.assertRaisesMessage(Exception, "Oops"):
                    with atomic:
                        Reporter.objects.create(first_name="Haddock")
                    raise Exception("Oops, that's his last name")
                raise Exception("Oops, that's his first name")
        self.assertSequenceEqual(Reporter.objects.all(), [])