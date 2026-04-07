def test_get_first_name(self):
        self.assertEqual(
            Author.objects.get(first_name__exact="John"),
            self.a1,
        )