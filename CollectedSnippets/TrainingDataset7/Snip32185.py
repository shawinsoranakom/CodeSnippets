def __call__(self, signal, sender, instance, origin, **kwargs):
                self.data.append((instance, sender, instance.id is None, origin))