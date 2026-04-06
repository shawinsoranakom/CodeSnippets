def fn(self):
        @cache('~/.bashrc')
        def fn():
            return 'test'

        return fn