def enqueue_callback(self, using="default"):
        def hook():
            self.callback_called = True

        transaction.on_commit(hook, using=using)