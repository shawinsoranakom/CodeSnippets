def test_eq(self):
        s1 = Secondary.objects.create(first="x1", second="y1")
        s1_defer = Secondary.objects.only("pk").get(pk=s1.pk)
        self.assertEqual(s1, s1_defer)
        self.assertEqual(s1_defer, s1)