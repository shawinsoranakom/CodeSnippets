def test_flatpage_admin_form_edit(self):
        """
        Existing flatpages can be edited in the admin form without triggering
        the url-uniqueness validation.
        """
        existing = FlatPage.objects.create(
            url="/myflatpage1/", title="Some page", content="The content"
        )
        existing.sites.add(settings.SITE_ID)

        data = dict(url="/myflatpage1/", **self.form_data)

        f = FlatpageForm(data=data, instance=existing)

        self.assertTrue(f.is_valid(), f.errors)

        updated = f.save()

        self.assertEqual(updated.title, "A test page")