def _set_list(self, length, items):
        # this would work:
        # self._list = self._mytype(items)
        # but then we wouldn't be testing length parameter
        itemList = ["x"] * length
        for i, v in enumerate(items):
            itemList[i] = v

        self._list = self._mytype(itemList)