def __le__(self, other):
            if isinstance(other, Promise):
                other = other.__cast()
            return self.__cast() <= other