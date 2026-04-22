def __setitem__(self, key, value) -> NoReturn:
        raise TypeError("Secrets does not support item assignment.")