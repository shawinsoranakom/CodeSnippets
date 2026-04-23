def __setattr__(self, key, value) -> NoReturn:
        raise TypeError("Secrets does not support attribute assignment.")