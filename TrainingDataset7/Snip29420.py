async def test_aget_page_empty_obj_list_and_allow_empty_first_page_false_async(
        self,
    ):
        """
        AsyncPaginator.aget_page() raises EmptyPage if
        allow_empty_first_page=False and object_list is empty.
        """
        paginator = AsyncPaginator([], 2, allow_empty_first_page=False)
        with self.assertRaises(EmptyPage):
            await paginator.aget_page(1)