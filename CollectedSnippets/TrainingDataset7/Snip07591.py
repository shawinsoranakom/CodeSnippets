def __init__(self, request, *args, **kwargs):
        self.request = request
        self._queued_messages = []
        self.used = False
        self.added_new = False
        super().__init__(*args, **kwargs)