def test_basic(self):
        authors = Author.objects.annotate(
            backward=Reverse("name"),
            constant=Reverse(Value("static string")),
        )
        self.assertQuerySetEqual(
            authors,
            [
                ("John Smith", "htimS nhoJ", "gnirts citats"),
                ("Élena Jordan", "nadroJ anelÉ", "gnirts citats"),
                ("パイソン", "ンソイパ", "gnirts citats"),
            ],
            lambda a: (a.name, a.backward, a.constant),
            ordered=False,
        )