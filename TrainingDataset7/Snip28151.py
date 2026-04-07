def test_slugfield_max_length(self):
        """
        SlugField honors max_length.
        """
        bs = BigS.objects.create(s="slug" * 50)
        bs = BigS.objects.get(pk=bs.pk)
        self.assertEqual(bs.s, "slug" * 50)