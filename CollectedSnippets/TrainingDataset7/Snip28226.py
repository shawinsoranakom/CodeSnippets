def test_blank_in_choices(self):
        choices = [("", "<><>"), ("a", "A")]
        f = models.CharField(choices=choices)
        self.assertEqual(f.get_choices(include_blank=True), choices)