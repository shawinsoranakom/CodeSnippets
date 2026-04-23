def __init__(self, queryset, page_size, orphans=0, allow_empty_first_page=True):
        super().__init__(
            queryset, 5, orphans=2, allow_empty_first_page=allow_empty_first_page
        )