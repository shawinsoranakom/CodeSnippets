def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(**{self._get_field_name() + "__id": settings.SITE_ID})
        )