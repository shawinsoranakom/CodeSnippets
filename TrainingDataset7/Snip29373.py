def test_reverse_ordering(self):
        self.assertIs(Author.objects.order_by("-pk").totally_ordered, True)