def setUpTestData(cls):
        # don't use the manager because we want to ensure the site exists
        # with pk=1, regardless of whether or not it already exists.
        cls.site1 = Site(pk=1, domain="example.com", name="example.com")
        cls.site1.save()
        cls.fp1 = FlatPage.objects.create(
            url="/flatpage/",
            title="A Flatpage",
            content="Isn't it flat!",
            enable_comments=False,
            template_name="",
            registration_required=False,
        )
        cls.fp2 = FlatPage.objects.create(
            url="/location/flatpage/",
            title="A Nested Flatpage",
            content="Isn't it flat and deep!",
            enable_comments=False,
            template_name="",
            registration_required=False,
        )
        cls.fp3 = FlatPage.objects.create(
            url="/sekrit/",
            title="Sekrit Flatpage",
            content="Isn't it sekrit!",
            enable_comments=False,
            template_name="",
            registration_required=True,
        )
        cls.fp4 = FlatPage.objects.create(
            url="/location/sekrit/",
            title="Sekrit Nested Flatpage",
            content="Isn't it sekrit and deep!",
            enable_comments=False,
            template_name="",
            registration_required=True,
        )
        cls.fp1.sites.add(cls.site1)
        cls.fp2.sites.add(cls.site1)
        cls.fp3.sites.add(cls.site1)
        cls.fp4.sites.add(cls.site1)