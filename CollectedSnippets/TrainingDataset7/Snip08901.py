def __init__(
        self,
        object_list,
        per_page,
        orphans=0,
        allow_empty_first_page=True,
        error_messages=None,
    ):
        self.object_list = object_list
        self._check_object_list_is_ordered()
        self.per_page = int(per_page)
        self.orphans = int(orphans)
        self.allow_empty_first_page = allow_empty_first_page
        self.error_messages = (
            self.default_error_messages
            if error_messages is None
            else self.default_error_messages | error_messages
        )
        if self.per_page <= self.orphans:
            # RemovedInDjango70Warning: When the deprecation ends, replace
            # with:
            # raise ValueError(
            #     "The orphans argument cannot be larger than or equal to the "
            #     "per_page argument."
            # )
            msg = (
                "Support for the orphans argument being larger than or equal to the "
                "per_page argument is deprecated. This will raise a ValueError in "
                "Django 7.0."
            )
            warnings.warn(msg, category=RemovedInDjango70Warning, stacklevel=2)