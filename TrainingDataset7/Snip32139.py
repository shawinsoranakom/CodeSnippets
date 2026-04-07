def test_disconnect_unregistered_model(self, apps):
        received = []

        def receiver(**kwargs):
            received.append(kwargs)

        signals.post_init.connect(receiver, sender="signals.Created", apps=apps)
        try:
            self.assertIsNone(
                signals.post_init.disconnect(
                    receiver, sender="signals.Created", apps=apps
                )
            )
            self.assertIsNone(
                signals.post_init.disconnect(
                    receiver, sender="signals.Created", apps=apps
                )
            )

            class Created(models.Model):
                pass

            Created()
            self.assertEqual(received, [])
        finally:
            signals.post_init.disconnect(receiver, sender="signals.Created")