def __reduce__(self):
            return (
                _lazy_proxy_unpickle,
                (func, self._args, self._kw, *resultclasses),
            )