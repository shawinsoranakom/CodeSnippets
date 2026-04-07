def __init__(
        self,
        template,
        context=None,
        content_type=None,
        status=None,
        charset=None,
        using=None,
        headers=None,
    ):
        # It would seem obvious to call these next two members 'template' and
        # 'context', but those names are reserved as part of the test Client
        # API. To avoid the name collision, we use different names.
        self.template_name = template
        self.context_data = context

        self.using = using

        self._post_render_callbacks = []

        # _request stores the current request object in subclasses that know
        # about requests, like TemplateResponse. It's defined in the base class
        # to minimize code duplication.
        # It's called self._request because self.request gets overwritten by
        # django.test.client.Client. Unlike template_name and context_data,
        # _request should not be considered part of the public API.
        self._request = None

        # content argument doesn't make sense here because it will be replaced
        # with rendered template so we always pass empty string in order to
        # prevent errors and provide shorter signature.
        super().__init__("", content_type, status, charset=charset, headers=headers)

        # _is_rendered tracks whether the template and context has been baked
        # into a final response.
        # Super __init__ doesn't know any better than to set self.content to
        # the empty string we just gave it, which wrongly sets _is_rendered
        # True, so we initialize it to False after the call to super __init__.
        self._is_rendered = False