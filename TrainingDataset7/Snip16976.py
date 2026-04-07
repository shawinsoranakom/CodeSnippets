def test_combine_different_types(self):
        msg = (
            "Cannot infer type of '+' expression involving these types: FloatField, "
            "DecimalField. You must set output_field."
        )
        qs = Book.objects.annotate(sums=Sum("rating") + Sum("pages") + Sum("price"))
        with self.assertRaisesMessage(FieldError, msg):
            qs.first()
        with self.assertRaisesMessage(FieldError, msg):
            qs.first()

        b1 = Book.objects.annotate(
            sums=Sum(F("rating") + F("pages") + F("price"), output_field=IntegerField())
        ).get(pk=self.b4.pk)
        self.assertEqual(b1.sums, 383)

        b2 = Book.objects.annotate(
            sums=Sum(F("rating") + F("pages") + F("price"), output_field=FloatField())
        ).get(pk=self.b4.pk)
        self.assertEqual(b2.sums, 383.69)

        b3 = Book.objects.annotate(
            sums=Sum(F("rating") + F("pages") + F("price"), output_field=DecimalField())
        ).get(pk=self.b4.pk)
        self.assertEqual(b3.sums, Approximate(Decimal("383.69"), places=2))