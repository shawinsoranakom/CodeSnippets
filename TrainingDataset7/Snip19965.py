def test_model_with_broken_get_absolute_url(self):
        """
        The view doesn't catch an AttributeError raised by
        Model.get_absolute_url() (#8997).
        """
        user_ct = ContentType.objects.get_for_model(FooWithBrokenAbsoluteUrl)
        obj = FooWithBrokenAbsoluteUrl.objects.create(name="john")
        with self.assertRaises(AttributeError):
            shortcut(self.request, user_ct.id, obj.id)