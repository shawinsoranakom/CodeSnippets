def test_compress_format_loading(self):
        # Load fixture 4 (compressed), using format specification
        management.call_command("loaddata", "fixture4.json", verbosity=0)
        self.assertEqual(Article.objects.get().headline, "Django pets kitten")