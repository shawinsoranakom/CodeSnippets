def test_hooks_cleared_on_reconnect(self):
        with transaction.atomic():
            self.do(1)
            connection.close()

        connection.connect()

        with transaction.atomic():
            self.do(2)

        self.assertDone([2])