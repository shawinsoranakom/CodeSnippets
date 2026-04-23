def __new__(cls, name=None, id=None):
        main, *_ = _interpreters.get_main()
        if id == main:
            if not name:
                name = 'main'
            elif name != 'main':
                raise ValueError(
                    'name mismatch (expected "main", got "{}")'.format(name))
            id = main
        elif id is not None:
            if not name:
                name = 'interp'
            elif name == 'main':
                raise ValueError('name mismatch (unexpected "main")')
            assert isinstance(id, int), repr(id)
        elif not name or name == 'main':
            name = 'main'
            id = main
        else:
            id = _interpreters.create()
        self = super().__new__(cls, name, id)
        return self