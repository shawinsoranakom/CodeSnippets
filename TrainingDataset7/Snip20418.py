def test_trunc_subquery_with_parameters(self):
        author_1 = Author.objects.create(name="J. R. R. Tolkien")
        author_2 = Author.objects.create(name="G. R. R. Martin")
        fan_since_1 = datetime.datetime(2016, 2, 3, 15, 0, 0)
        fan_since_2 = datetime.datetime(2015, 2, 3, 15, 0, 0)
        fan_since_3 = datetime.datetime(2017, 2, 3, 15, 0, 0)
        if settings.USE_TZ:
            fan_since_1 = timezone.make_aware(fan_since_1)
            fan_since_2 = timezone.make_aware(fan_since_2)
            fan_since_3 = timezone.make_aware(fan_since_3)
        Fan.objects.create(author=author_1, name="Tom", fan_since=fan_since_1)
        Fan.objects.create(author=author_1, name="Emma", fan_since=fan_since_2)
        Fan.objects.create(author=author_2, name="Isabella", fan_since=fan_since_3)

        inner = (
            Fan.objects.filter(
                author=OuterRef("pk"), name__in=("Emma", "Isabella", "Tom")
            )
            .values("author")
            .annotate(newest_fan=Max("fan_since"))
            .values("newest_fan")
        )
        outer = Author.objects.annotate(
            newest_fan_year=TruncYear(Subquery(inner, output_field=DateTimeField()))
        )
        tz = datetime.UTC if settings.USE_TZ else None
        self.assertSequenceEqual(
            outer.order_by("name").values("name", "newest_fan_year"),
            [
                {
                    "name": "G. R. R. Martin",
                    "newest_fan_year": datetime.datetime(2017, 1, 1, 0, 0, tzinfo=tz),
                },
                {
                    "name": "J. R. R. Tolkien",
                    "newest_fan_year": datetime.datetime(2016, 1, 1, 0, 0, tzinfo=tz),
                },
            ],
        )