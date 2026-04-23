def test_shortcut_with_absolute_url_including_scheme(self):
        """
        Can view a shortcut when object's get_absolute_url returns a full URL
        the tested URLs are: "http://...", "https://..." and "//..."
        """
        for obj in SchemeIncludedURL.objects.all():
            with self.subTest(obj=obj):
                short_url = "/shortcut/%s/%s/" % (
                    ContentType.objects.get_for_model(SchemeIncludedURL).id,
                    obj.pk,
                )
                response = self.client.get(short_url)
                self.assertRedirects(
                    response, obj.get_absolute_url(), fetch_redirect_response=False
                )