def setUpTestData(cls):
        slugs = [
            "a",
            "a/a",
            "a/b",
            "a/b/a",
            "x",
            "x/y/z",
        ]
        SlugPage.objects.bulk_create([SlugPage(slug=slug) for slug in slugs])