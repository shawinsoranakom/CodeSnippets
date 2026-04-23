def test_empty_join_conditions(self):
        x = SlugPage.objects.get(slug="x")
        message = "Join generated an empty ON clause."
        with self.assertRaisesMessage(ValueError, message):
            list(SlugPage.objects.filter(containers=x))