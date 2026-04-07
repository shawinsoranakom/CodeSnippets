def test_complex_annotations_must_have_an_alias(self):
        complex_annotations = [
            F("rating") * F("price"),
            Value("title"),
            Case(When(pages__gte=400, then=Value("Long")), default=Value("Short")),
            Subquery(
                Book.objects.filter(publisher_id=OuterRef("pk"))
                .order_by("-pubdate")
                .values("name")[:1]
            ),
            Exists(Book.objects.filter(publisher_id=OuterRef("pk"))),
        ]
        msg = "Complex annotations require an alias"
        for annotation in complex_annotations:
            with self.subTest(annotation=annotation):
                with self.assertRaisesMessage(TypeError, msg):
                    Book.objects.annotate(annotation)