def __radd__(self, other):
            return other + self.__cast()