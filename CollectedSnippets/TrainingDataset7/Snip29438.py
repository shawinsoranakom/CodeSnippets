async def test_paginating_unordered_object_list_raises_warning_async(self):
        """
        See test_paginating_unordered_object_list_raises_warning.
        """

        class ObjectList:
            ordered = False

        object_list = ObjectList()
        msg = (
            "Pagination may yield inconsistent results with an unordered "
            "object_list: {!r}.".format(object_list)
        )
        with self.assertWarnsMessage(UnorderedObjectListWarning, msg):
            AsyncPaginator(object_list, 5)