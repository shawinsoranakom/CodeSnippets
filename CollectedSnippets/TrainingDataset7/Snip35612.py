def test_nested_inner_durable(self):
        msg = "A durable atomic block cannot be nested within another atomic block."
        with transaction.atomic():
            with self.assertRaisesMessage(RuntimeError, msg):
                with transaction.atomic(durable=True):
                    pass