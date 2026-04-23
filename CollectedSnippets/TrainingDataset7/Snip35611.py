def test_nested_both_durable(self):
        msg = "A durable atomic block cannot be nested within another atomic block."
        with transaction.atomic(durable=True):
            with self.assertRaisesMessage(RuntimeError, msg):
                with transaction.atomic(durable=True):
                    pass