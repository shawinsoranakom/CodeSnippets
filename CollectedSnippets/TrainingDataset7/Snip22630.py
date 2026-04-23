def __init__(self, object_hook=None, *args, **kwargs):
                return super().__init__(object_hook=self.as_uuid, *args, **kwargs)