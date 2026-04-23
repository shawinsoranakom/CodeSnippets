def test_ticket3141(self):
        self.assertEqual(Author.objects.extra(select={"foo": "1"}).count(), 4)
        self.assertEqual(
            Author.objects.extra(select={"foo": "%s"}, select_params=(1,)).count(), 4
        )