def _make_books(n, base_date):
    for i in range(n):
        Book.objects.create(
            name="Book %d" % i,
            slug="book-%d" % i,
            pages=100 + i,
            pubdate=base_date - datetime.timedelta(days=i),
        )