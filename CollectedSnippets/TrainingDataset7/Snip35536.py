def do(self, num):
        """Create a Thing instance and notify about it."""
        Thing.objects.create(num=num)
        transaction.on_commit(lambda: self.notify(num))