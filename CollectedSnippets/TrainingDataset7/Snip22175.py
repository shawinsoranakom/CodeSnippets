def test_compressed_loading_xz(self):
        management.call_command("loaddata", "fixture5.json.xz", verbosity=0)
        self.assertEqual(
            Article.objects.get().headline,
            "WoW subscribers now outnumber readers",
        )