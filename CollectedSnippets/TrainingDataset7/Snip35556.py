def test_error_in_hook_doesnt_prevent_clearing_hooks(self):
        try:
            with transaction.atomic():
                transaction.on_commit(lambda: self.notify("error"))
        except ForcedError:
            pass

        with transaction.atomic():
            self.do(1)

        self.assertDone([1])