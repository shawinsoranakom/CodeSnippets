class LinkedDeque(_DoublyLinkedBase):
    def first(self):
        if self.is_empty():
            raise Exception("List is empty")
        return self._header._next._data

    def last(self):
        if self.is_empty():
            raise Exception("List is empty")
        return self._trailer._prev._data

    def add_first(self, element):
        return self._insert(self._header, element, self._header._next)

    def add_last(self, element):
        return self._insert(self._trailer._prev, element, self._trailer)


    def remove_first(self):
        if self.is_empty():
            raise IndexError("remove_first from empty list")
        return self._delete(self._header._next)

    def remove_last(self):
        if self.is_empty():
            raise IndexError("remove_first from empty list")
        return self._delete(self._trailer._prev)
