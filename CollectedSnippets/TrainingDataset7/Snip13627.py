def __init__(
        self,
        *,
        json_encoder=DjangoJSONEncoder,
        headers=None,
        query_params=None,
        **defaults,
    ):
        self.json_encoder = json_encoder
        self.defaults = defaults
        self.cookies = SimpleCookie()
        self.errors = BytesIO()
        if headers:
            self.defaults.update(HttpHeaders.to_wsgi_names(headers))
        if query_params:
            self.defaults["QUERY_STRING"] = urlencode(query_params, doseq=True)