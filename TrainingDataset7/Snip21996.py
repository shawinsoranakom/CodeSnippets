def __init__(self, request=None):
        from .tests import UPLOAD_TO

        super().__init__(request)
        self.upload_dir = UPLOAD_TO