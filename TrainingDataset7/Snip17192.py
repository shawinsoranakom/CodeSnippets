def test_filter_decimal_annotation(self):
        qs = (
            Book.objects.annotate(new_price=F("price") + 1)
            .filter(new_price=Decimal(31))
            .values_list("new_price")
        )
        self.assertEqual(qs.get(), (Decimal(31),))