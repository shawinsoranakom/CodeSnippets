def test_raises_exception_non_callable(self):
        msg = "on_commit()'s callback must be a callable."
        with self.assertRaisesMessage(TypeError, msg):
            transaction.on_commit(None)