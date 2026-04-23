def __init__(self, root=None, parent=None, sampled=None, data=None, lineage=None):
        """
        :param str root: trace id
        :param str parent: parent id
        :param int sampled: 0 means not sampled, 1 means sampled
        :param dict data: arbitrary data fields
        :param str lineage: lineage
        """
        self._root = root
        self._parent = parent
        self._sampled = None
        self._lineage = lineage
        self._data = data

        if sampled is not None:
            if sampled == "?":
                self._sampled = sampled
            if sampled is True or sampled == "1" or sampled == 1:
                self._sampled = 1
            if sampled is False or sampled == "0" or sampled == 0:
                self._sampled = 0