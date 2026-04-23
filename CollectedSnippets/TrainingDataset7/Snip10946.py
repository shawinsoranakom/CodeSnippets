def __init__(self, queryset, output_field=None, **extra):
        # Allow the usage of both QuerySet and sql.Query objects.
        self.query = getattr(queryset, "query", queryset).clone()
        self.query.subquery = True
        self.template = extra.pop("template", self.template)
        self.extra = extra
        super().__init__(output_field)