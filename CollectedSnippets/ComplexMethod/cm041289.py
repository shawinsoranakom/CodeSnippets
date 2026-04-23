def get_page(
        self,
        token_generator: Callable[[_E], str],
        next_token: str = None,
        page_size: int = None,
        filter_function: Callable[[_E], bool] = None,
    ) -> tuple[list[_E], str | None]:
        if filter_function is not None:
            result_list = list(filter(filter_function, self))
        else:
            result_list = self

        if page_size is None:
            page_size = self.DEFAULT_PAGE_SIZE

        # returns all or remaining elements in final page.
        if len(result_list) <= page_size and next_token is None:
            return result_list, None

        start_idx = 0

        try:
            start_item = next(item for item in result_list if token_generator(item) == next_token)
            start_idx = result_list.index(start_item)
        except StopIteration:
            pass

        if start_idx + page_size < len(result_list):
            next_token = token_generator(result_list[start_idx + page_size])
        else:
            next_token = None

        return result_list[start_idx : start_idx + page_size], next_token