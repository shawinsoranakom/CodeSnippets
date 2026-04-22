def __init__(self, kind: MediaFileKind = MediaFileKind.MEDIA):
        self._kind = kind
        self._is_marked_for_delete = False