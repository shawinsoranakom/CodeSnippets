def test_slugfield_unicode_max_length(self):
        """
        SlugField with allow_unicode=True honors max_length.
        """
        bs = UnicodeSlugField.objects.create(s="你好你好" * 50)
        bs = UnicodeSlugField.objects.get(pk=bs.pk)
        self.assertEqual(bs.s, "你好你好" * 50)