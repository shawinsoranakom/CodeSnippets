def test_annotate_on_relation(self):
        book = Book.objects.annotate(
            avg_price=Avg("price"), publisher_name=F("publisher__name")
        ).get(pk=self.b1.pk)
        self.assertEqual(book.avg_price, 30.00)
        self.assertEqual(book.publisher_name, "Apress")