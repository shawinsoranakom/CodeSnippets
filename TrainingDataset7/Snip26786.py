def test_persistence(self):
        self.assertEqual(
            Book.objects.count(),
            1,
        )