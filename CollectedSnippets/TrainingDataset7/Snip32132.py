def test_disconnect_model(self, apps):
        received = []

        def receiver(**kwargs):
            received.append(kwargs)

        class Created(models.Model):
            pass

        signals.post_init.connect(receiver, sender=Created, apps=apps)
        try:
            self.assertIs(
                signals.post_init.disconnect(receiver, sender=Created, apps=apps),
                True,
            )
            self.assertIs(
                signals.post_init.disconnect(receiver, sender=Created, apps=apps),
                False,
            )
            Created()
            self.assertEqual(received, [])
        finally:
            signals.post_init.disconnect(receiver, sender=Created)