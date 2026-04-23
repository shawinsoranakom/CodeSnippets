def call(self, *args, **kwargs):
        if iscoroutinefunction(self.func):
            return async_to_sync(self.func)(*args, **kwargs)
        return self.func(*args, **kwargs)