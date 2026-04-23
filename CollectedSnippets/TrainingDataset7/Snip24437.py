def __init__(self, i_list, *args, **kwargs):
        self._list = self._mytype(i_list)
        super().__init__(*args, **kwargs)