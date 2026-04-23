def test_reuse_rollback_commit(self):
        atomic = transaction.atomic()
        with self.assertRaisesMessage(Exception, "Oops"):
            with atomic:
                Reporter.objects.create(last_name="Tintin")
                with atomic:
                    Reporter.objects.create(last_name="Haddock")
                raise Exception("Oops, that's his first name")
        self.assertSequenceEqual(Reporter.objects.all(), [])