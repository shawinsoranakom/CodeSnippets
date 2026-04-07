def test_compressed_specified_loading(self):
        # Load fixture 5 (compressed), using format *and* compression
        # specification
        management.call_command("loaddata", "fixture5.json.zip", verbosity=0)
        self.assertEqual(
            Article.objects.get().headline,
            "WoW subscribers now outnumber readers",
        )