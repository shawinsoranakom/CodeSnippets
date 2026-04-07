def setUp(self):
        self.client.force_login(self.user)
        self.signals = []

        pre_save.connect(self.pre_save_listener, sender=LogEntry)
        self.addCleanup(pre_save.disconnect, self.pre_save_listener, sender=LogEntry)

        post_save.connect(self.post_save_listener, sender=LogEntry)
        self.addCleanup(post_save.disconnect, self.post_save_listener, sender=LogEntry)