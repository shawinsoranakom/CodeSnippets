def test_compressed_loading_gzip(self):
        management.call_command("loaddata", "fixture5.json.gz", verbosity=0)
        self.assertEqual(
            Article.objects.get().headline,
            "WoW subscribers now outnumber readers",
        )