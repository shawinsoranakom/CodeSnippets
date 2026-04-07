def test_discards_hooks_from_rolled_back_savepoint(self):
        with transaction.atomic():
            # one successful savepoint
            with transaction.atomic():
                self.do(1)
            # one failed savepoint
            try:
                with transaction.atomic():
                    self.do(2)
                    raise ForcedError()
            except ForcedError:
                pass
            # another successful savepoint
            with transaction.atomic():
                self.do(3)

        # only hooks registered during successful savepoints execute
        self.assertDone([1, 3])