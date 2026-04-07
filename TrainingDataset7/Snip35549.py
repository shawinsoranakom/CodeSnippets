def test_inner_savepoint_rolled_back_with_outer(self):
        with transaction.atomic():
            try:
                with transaction.atomic():
                    with transaction.atomic():
                        self.do(1)
                    raise ForcedError()
            except ForcedError:
                pass
            self.do(2)

        self.assertDone([2])