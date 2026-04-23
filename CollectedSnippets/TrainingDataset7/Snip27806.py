def test_charfield_with_choices_cleans_valid_choice(self):
        f = models.CharField(max_length=1, choices=[("a", "A"), ("b", "B")])
        self.assertEqual("a", f.clean("a", None))