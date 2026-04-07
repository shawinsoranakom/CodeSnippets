def lazy_wrap(self, wrapped_object):
        return SimpleLazyObject(lambda: wrapped_object)