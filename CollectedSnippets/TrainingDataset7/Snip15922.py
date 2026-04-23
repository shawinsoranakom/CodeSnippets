def post_save_listener(self, instance, created, **kwargs):
        self.signals.append(("post_save", instance, created))