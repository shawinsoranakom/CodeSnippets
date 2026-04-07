def __contains__(self, element):
        return self._count(element, count=False) > 0