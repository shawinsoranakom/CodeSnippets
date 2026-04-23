def setUp(self):
        self.pre_delete_senders = []
        self.post_delete_senders = []
        for sender in self.senders:
            models.signals.pre_delete.connect(self.pre_delete_receiver, sender)
            self.addCleanup(
                models.signals.pre_delete.disconnect, self.pre_delete_receiver, sender
            )
            models.signals.post_delete.connect(self.post_delete_receiver, sender)
            self.addCleanup(
                models.signals.post_delete.disconnect, self.post_delete_receiver, sender
            )