def __init__(self, trans=None):
        self._catalogs = [trans._catalog.copy()] if trans else [{}]
        self._plurals = [trans.plural] if trans else [lambda n: int(n != 1)]