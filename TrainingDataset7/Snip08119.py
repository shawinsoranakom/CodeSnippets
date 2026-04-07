def __init__(self, storage=None, *args, **kwargs):
        if storage is not None:
            self.storage = storage
        if self.storage is None:
            raise ImproperlyConfigured(
                "The staticfiles storage finder %r "
                "doesn't have a storage class "
                "assigned." % self.__class__
            )
        # Make sure we have a storage instance here.
        if not isinstance(self.storage, (Storage, LazyObject)):
            self.storage = self.storage()
        super().__init__(*args, **kwargs)