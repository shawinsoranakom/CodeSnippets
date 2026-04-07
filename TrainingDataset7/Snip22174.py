def test_compressed_loading_lzma(self):
        management.call_command("loaddata", "fixture5.json.lzma", verbosity=0)
        self.assertEqual(
            Article.objects.get().headline,
            "WoW subscribers now outnumber readers",
        )