def test_compressed_loading_bz2(self):
        management.call_command("loaddata", "fixture5.json.bz2", verbosity=0)
        self.assertEqual(
            Article.objects.get().headline,
            "WoW subscribers now outnumber readers",
        )