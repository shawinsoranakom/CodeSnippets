def setUp(self):
        self.signals_count = 0
        post_save.connect(self.post_save_listener, sender=User)
        self.addCleanup(post_save.disconnect, self.post_save_listener, sender=User)