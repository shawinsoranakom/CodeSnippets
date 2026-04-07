def test_model_without_get_absolute_url(self):
        """The view returns 404 when Model.get_absolute_url() isn't defined."""
        user_ct = ContentType.objects.get_for_model(FooWithoutUrl)
        obj = FooWithoutUrl.objects.create(name="john")
        with self.assertRaises(Http404):
            shortcut(self.request, user_ct.id, obj.id)