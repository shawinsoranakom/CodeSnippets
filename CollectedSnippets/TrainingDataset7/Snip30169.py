def test_prefetch_eq(self):
        prefetch_1 = Prefetch("authors", queryset=Author.objects.all())
        prefetch_2 = Prefetch("books", queryset=Book.objects.all())
        self.assertEqual(prefetch_1, prefetch_1)
        self.assertEqual(prefetch_1, mock.ANY)
        self.assertNotEqual(prefetch_1, prefetch_2)