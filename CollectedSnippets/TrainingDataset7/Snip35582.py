def test_merged_rollback_commit(self):
        with self.assertRaisesMessage(Exception, "Oops"):
            with transaction.atomic():
                Reporter.objects.create(last_name="Tintin")
                with transaction.atomic(savepoint=False):
                    Reporter.objects.create(last_name="Haddock")
                raise Exception("Oops, that's his first name")
        self.assertSequenceEqual(Reporter.objects.all(), [])