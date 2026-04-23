def test_loading_with_exclude_model(self):
        Site.objects.all().delete()
        management.call_command(
            "loaddata", "fixture1", exclude=["fixtures.Article"], verbosity=0
        )
        self.assertFalse(Article.objects.exists())
        self.assertEqual(Category.objects.get().title, "News Stories")
        self.assertEqual(Site.objects.get().domain, "example.com")