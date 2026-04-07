def test_shortcut_with_absolute_url(self):
        """
        Can view a shortcut for an Author object that has a get_absolute_url
        method
        """
        for obj in Author.objects.all():
            with self.subTest(obj=obj):
                short_url = "/shortcut/%s/%s/" % (
                    ContentType.objects.get_for_model(Author).id,
                    obj.pk,
                )
                response = self.client.get(short_url)
                self.assertRedirects(
                    response,
                    "http://testserver%s" % obj.get_absolute_url(),
                    target_status_code=404,
                )