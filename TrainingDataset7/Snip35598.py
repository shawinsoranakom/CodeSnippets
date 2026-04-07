def test_atomic_prevents_queries_in_broken_transaction(self):
        r1 = Reporter.objects.create(first_name="Archibald", last_name="Haddock")
        with transaction.atomic():
            r2 = Reporter(first_name="Cuthbert", last_name="Calculus", id=r1.id)
            with self.assertRaises(IntegrityError):
                r2.save(force_insert=True)
            # The transaction is marked as needing rollback.
            msg = (
                "An error occurred in the current transaction. You can't "
                "execute queries until the end of the 'atomic' block."
            )
            with self.assertRaisesMessage(
                transaction.TransactionManagementError, msg
            ) as cm:
                r2.save(force_update=True)
        self.assertIsInstance(cm.exception.__cause__, IntegrityError)
        self.assertEqual(Reporter.objects.get(pk=r1.pk).last_name, "Haddock")