def __reduce_ex__(self, protocol):
        raise PicklingError(f"Cannot pickle {self.__class__.__qualname__}.")