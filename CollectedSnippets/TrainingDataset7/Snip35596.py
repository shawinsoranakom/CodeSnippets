def test_atomic_prevents_setting_autocommit(self):
        autocommit = transaction.get_autocommit()
        with transaction.atomic():
            with self.assertRaisesMessage(
                transaction.TransactionManagementError, self.forbidden_atomic_msg
            ):
                transaction.set_autocommit(not autocommit)
        # Make sure autocommit wasn't changed.
        self.assertEqual(connection.autocommit, autocommit)