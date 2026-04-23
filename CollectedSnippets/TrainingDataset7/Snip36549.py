def __init__(self, baz):
        self.__dict__ = baz.__dict__
        self._baz = baz
        # Grandparent super
        super(BaseBaz, self).__init__()