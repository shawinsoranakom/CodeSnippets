def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(favorite_avg=models.Avg("favorite_books__favorite_thing_id"))
        )