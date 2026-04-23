def test_transaction_in_hook(self):
        def on_commit():
            with transaction.atomic():
                t = Thing.objects.create(num=1)
                self.notify(t.num)

        with transaction.atomic():
            transaction.on_commit(on_commit)

        self.assertDone([1])