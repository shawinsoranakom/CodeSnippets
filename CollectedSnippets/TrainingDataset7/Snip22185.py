def test_loading_with_exclude_app(self):
        Site.objects.all().delete()
        management.call_command(
            "loaddata", "fixture1", exclude=["fixtures"], verbosity=0
        )
        self.assertFalse(Article.objects.exists())
        self.assertFalse(Category.objects.exists())
        self.assertEqual(Site.objects.get().domain, "example.com")