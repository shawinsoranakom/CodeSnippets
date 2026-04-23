def __init__(self, queryset, **kwargs):
        super().__init__(queryset, **kwargs)
        self.query = self.query.exists()