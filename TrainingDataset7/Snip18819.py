def test_signal(self):
        data = {}

        def receiver(sender, connection, **kwargs):
            data["connection"] = connection

        connection_created.connect(receiver)
        connection.close()
        with connection.cursor():
            pass
        self.assertIs(data["connection"].connection, connection.connection)

        connection_created.disconnect(receiver)
        data.clear()
        with connection.cursor():
            pass
        self.assertEqual(data, {})