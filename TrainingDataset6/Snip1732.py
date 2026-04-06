def shelve(self, mocker):
        value = {}

        class _Shelve(object):
            def __init__(self, path):
                pass

            def __setitem__(self, k, v):
                value[k] = v

            def __getitem__(self, k):
                return value[k]

            def get(self, k, v=None):
                return value.get(k, v)

            def close(self):
                return

        mocker.patch('thefuck.utils.shelve.open', new_callable=lambda: _Shelve)
        return value