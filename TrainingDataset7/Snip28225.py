def test_empty_choices(self):
        choices = []
        f = models.CharField(choices=choices)
        self.assertEqual(f.get_choices(include_blank=False), choices)