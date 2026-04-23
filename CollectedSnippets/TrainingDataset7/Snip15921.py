def pre_save_listener(self, instance, **kwargs):
        self.signals.append(("pre_save", instance))