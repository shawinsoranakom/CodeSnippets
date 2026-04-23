def test_inner_savepoint_does_not_affect_outer(self):
        with transaction.atomic():
            with transaction.atomic():
                self.do(1)
                try:
                    with transaction.atomic():
                        raise ForcedError()
                except ForcedError:
                    pass

        self.assertDone([1])