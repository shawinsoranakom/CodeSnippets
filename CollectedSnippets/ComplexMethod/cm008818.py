def update(self, other, /, **kwargs) -> None:
        if isinstance(other, type(self)):
            other = other.sensitive()
        if isinstance(other, collections.abc.Mapping):
            for key, value in other.items():
                self[key] = value

        elif hasattr(other, 'keys'):
            for key in other.keys():  # noqa: SIM118
                self[key] = other[key]

        else:
            for key, value in other:
                self[key] = value

        for key, value in kwargs.items():
            self[key] = value