def test_nested_commit_rollback(self):
        with transaction.atomic():
            reporter = Reporter.objects.create(first_name="Tintin")
            with self.assertRaisesMessage(Exception, "Oops"):
                with transaction.atomic():
                    Reporter.objects.create(first_name="Haddock")
                    raise Exception("Oops, that's his last name")
        self.assertSequenceEqual(Reporter.objects.all(), [reporter])