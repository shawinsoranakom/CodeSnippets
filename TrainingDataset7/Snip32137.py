def test_not_loaded_model(self, apps):
        signals.post_init.connect(
            self.receiver, sender="signals.Created", weak=False, apps=apps
        )

        try:

            class Created(models.Model):
                pass

            instance = Created()
            self.assertEqual(
                self.received,
                [
                    {
                        "signal": signals.post_init,
                        "sender": Created,
                        "instance": instance,
                    }
                ],
            )
        finally:
            signals.post_init.disconnect(self.receiver, sender=Created)