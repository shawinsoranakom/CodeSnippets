def __init__(
        self,
        data=None,
        files=None,
        auto_id="id_%s",
        prefix=None,
        queryset=None,
        *,
        initial=None,
        **kwargs,
    ):
        self.queryset = queryset
        self.initial_extra = initial
        super().__init__(
            **{
                "data": data,
                "files": files,
                "auto_id": auto_id,
                "prefix": prefix,
                **kwargs,
            }
        )