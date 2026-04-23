def test_reverse_by_field(self):
        u1 = User.objects.get(poll__question__exact="What's the first question?")
        self.assertEqual(u1.name, "John Doe")

        u2 = User.objects.get(poll__question__exact="What's the second question?")
        self.assertEqual(u2.name, "Jim Bo")