def test_merged_inner_savepoint_rollback(self):
        with transaction.atomic():
            reporter = Reporter.objects.create(first_name="Tintin")
            with transaction.atomic():
                Reporter.objects.create(first_name="Archibald", last_name="Haddock")
                with self.assertRaisesMessage(Exception, "Oops"):
                    with transaction.atomic(savepoint=False):
                        Reporter.objects.create(first_name="Calculus")
                        raise Exception("Oops, that's his last name")
                # The third insert couldn't be roll back. Temporarily mark the
                # connection as not needing rollback to check it.
                self.assertTrue(transaction.get_rollback())
                transaction.set_rollback(False)
                self.assertEqual(Reporter.objects.count(), 3)
                transaction.set_rollback(True)
            # The second block has a savepoint and must roll back.
            self.assertEqual(Reporter.objects.count(), 1)
        self.assertSequenceEqual(Reporter.objects.all(), [reporter])