class _DoublyLinkedBase:

    class _Node:
        __slots__ = "_data", "_next", "_prev"

        def __init__(self, link_p, element, link_n):
            self._prev = link_p
            self._data = element
            self._next = link_n

        def has_next_and_prev(self):
            return (
                f" Prev -> {self._prev is not None}, Next -> {self._next is not None}"
            )

    def __init__(self):
        self._header = self._Node(None, None, None)
        self._trailer = self._Node(None, None, None)
        self._header._next = self._trailer
        self._trailer._prev = self._header
        self._size = 0

    def __len__(self):
        return self._size

    def is_empty(self):
        return self.__len__() == 0

    def _insert(self, predecessor, e, successor):
        new_node = self._Node(predecessor, e, successor)
        predecessor._next = new_node
        successor._prev = new_node
        self._size += 1
        return self

    def _delete(self, node):
        predecessor = node._prev
        successor = node._next

        predecessor._next = successor
        successor._prev = predecessor
        self._size -= 1
        temp = node._data
        node._prev = node._next = node._data = None
        del node
        return temp
