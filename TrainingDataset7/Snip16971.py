def test_nonfield_annotation(self):
        book = Book.objects.annotate(val=Max(Value(2))).first()
        self.assertEqual(book.val, 2)
        book = Book.objects.annotate(
            val=Max(Value(2), output_field=IntegerField())
        ).first()
        self.assertEqual(book.val, 2)
        book = Book.objects.annotate(val=Max(2, output_field=IntegerField())).first()
        self.assertEqual(book.val, 2)