def __call__(self, signal, sender, **kwargs):
        self._database = kwargs["using"]