def test_already_loaded_model(self):
        signals.post_init.connect(self.receiver, sender="signals.Book", weak=False)
        try:
            instance = Book()
            self.assertEqual(
                self.received,
                [{"signal": signals.post_init, "sender": Book, "instance": instance}],
            )
        finally:
            signals.post_init.disconnect(self.receiver, sender=Book)