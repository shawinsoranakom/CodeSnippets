def __init__(
        self,
        object_list,
        per_page,
        orphans=0,
        allow_empty_first_page=True,
        error_messages=None,
    ):
        super().__init__(
            object_list, per_page, orphans, allow_empty_first_page, error_messages
        )
        self._cache_acount = None
        self._cache_anum_pages = None