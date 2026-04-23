def test_decimal_max_digits_has_no_effect(self):
        Book.objects.all().delete()
        a1 = Author.objects.first()
        p1 = Publisher.objects.first()
        thedate = timezone.now()
        for i in range(10):
            Book.objects.create(
                isbn="abcde{}".format(i),
                name="none",
                pages=10,
                rating=4.0,
                price=9999.98,
                contact=a1,
                publisher=p1,
                pubdate=thedate,
            )

        book = Book.objects.aggregate(price_sum=Sum("price"))
        self.assertEqual(book["price_sum"], Decimal("99999.80"))