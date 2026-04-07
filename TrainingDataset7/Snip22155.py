def test_load_fixture_with_special_characters(self):
        management.call_command("loaddata", "fixture_with[special]chars", verbosity=0)
        self.assertEqual(
            Article.objects.get().headline,
            "How To Deal With Special Characters",
        )