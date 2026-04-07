def __init__(
        self,
        request,
        template,
        context=None,
        content_type=None,
        status=None,
        charset=None,
        using=None,
        headers=None,
    ):
        super().__init__(
            template, context, content_type, status, charset, using, headers=headers
        )
        self._request = request