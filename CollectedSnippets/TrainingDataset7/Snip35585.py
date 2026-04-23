def test_reuse_commit_rollback(self):
        atomic = transaction.atomic()
        with atomic:
            reporter = Reporter.objects.create(first_name="Tintin")
            with self.assertRaisesMessage(Exception, "Oops"):
                with atomic:
                    Reporter.objects.create(first_name="Haddock")
                    raise Exception("Oops, that's his last name")
        self.assertSequenceEqual(Reporter.objects.all(), [reporter])