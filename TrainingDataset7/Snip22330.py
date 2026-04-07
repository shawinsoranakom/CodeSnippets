def setUpTestData(cls):
        Site = apps.get_model("sites.Site")
        current_site = Site.objects.get_current()
        current_site.flatpage_set.create(url="/foo/", title="foo")
        current_site.flatpage_set.create(
            url="/private-foo/", title="private foo", registration_required=True
        )