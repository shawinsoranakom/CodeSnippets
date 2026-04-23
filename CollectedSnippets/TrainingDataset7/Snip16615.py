def test_readonly_field_overrides(self):
        """
        Regression test for #22087 - ModelForm Meta overrides are ignored by
        AdminReadonlyField
        """
        p = FieldOverridePost.objects.create(title="Test Post", content="Test Content")
        response = self.client.get(
            reverse("admin:admin_views_fieldoverridepost_change", args=(p.pk,))
        )
        self.assertContains(
            response,
            '<div class="help"><div>Overridden help text for the date</div></div>',
            html=True,
        )
        self.assertContains(
            response,
            '<label for="id_public">Overridden public label:</label>',
            html=True,
        )
        self.assertNotContains(
            response, "Some help text for the date (with Unicode ŠĐĆŽćžšđ)"
        )