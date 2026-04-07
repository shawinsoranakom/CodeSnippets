def __call__(self, signal, sender, **kwargs):
                self._run = True
                signal.disconnect(receiver=self, sender=sender)