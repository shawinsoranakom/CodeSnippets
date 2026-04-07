def test_shortcut_view_with_null_site_fk(self, get_model):
        """
        The shortcut view works if a model's ForeignKey to site is None.
        """
        get_model.side_effect = lambda *args, **kwargs: (
            MockSite if args[0] == "sites.Site" else ModelWithNullFKToSite
        )

        obj = ModelWithNullFKToSite.objects.create(title="title")
        url = "/shortcut/%s/%s/" % (
            ContentType.objects.get_for_model(ModelWithNullFKToSite).id,
            obj.pk,
        )
        response = self.client.get(url)
        expected_url = "http://example.com%s" % obj.get_absolute_url()
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)