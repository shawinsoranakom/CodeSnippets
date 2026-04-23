def test_shortcut_no_absolute_url(self):
        """
        Shortcuts for an object that has no get_absolute_url() method raise
        404.
        """
        for obj in Article.objects.all():
            with self.subTest(obj=obj):
                short_url = "/shortcut/%s/%s/" % (
                    ContentType.objects.get_for_model(Article).id,
                    obj.pk,
                )
                response = self.client.get(short_url)
                self.assertEqual(response.status_code, 404)