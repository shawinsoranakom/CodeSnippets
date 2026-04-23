def test_compressed_loading(self):
        # Load fixture 5 (compressed), only compression specification
        management.call_command("loaddata", "fixture5.zip", verbosity=0)
        self.assertEqual(
            Article.objects.get().headline,
            "WoW subscribers now outnumber readers",
        )