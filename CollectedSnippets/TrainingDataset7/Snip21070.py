def pre_delete_receiver(self, sender, **kwargs):
        self.pre_delete_senders.append(sender)