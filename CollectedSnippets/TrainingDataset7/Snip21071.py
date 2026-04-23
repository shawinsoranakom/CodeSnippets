def post_delete_receiver(self, sender, **kwargs):
        self.post_delete_senders.append(sender)