def setUpTestData(cls):
        author = Author.objects.create(name="Author")
        editor = Editor.objects.create(name="Editor")
        cls.book1 = Book.objects.create(
            title="Poem by Alice",
            editor=editor,
            author=author,
        )
        cls.book2 = Book.objects.create(
            title="The book by Jane A",
            editor=editor,
            author=author,
        )
        cls.book3 = Book.objects.create(
            title="The book by Jane B",
            editor=editor,
            author=author,
        )
        cls.seller1 = Seller.objects.create(name="Seller 1")
        cls.seller2 = Seller.objects.create(name="Seller 2")
        cls.usd = Currency.objects.create(currency="USD")
        cls.eur = Currency.objects.create(currency="EUR")
        cls.sales_date1 = date(2020, 7, 6)
        cls.sales_date2 = date(2020, 7, 7)
        ExchangeRate.objects.bulk_create(
            [
                ExchangeRate(
                    rate_date=cls.sales_date1,
                    from_currency=cls.usd,
                    to_currency=cls.eur,
                    rate=0.40,
                ),
                ExchangeRate(
                    rate_date=cls.sales_date1,
                    from_currency=cls.eur,
                    to_currency=cls.usd,
                    rate=1.60,
                ),
                ExchangeRate(
                    rate_date=cls.sales_date2,
                    from_currency=cls.usd,
                    to_currency=cls.eur,
                    rate=0.50,
                ),
                ExchangeRate(
                    rate_date=cls.sales_date2,
                    from_currency=cls.eur,
                    to_currency=cls.usd,
                    rate=1.50,
                ),
                ExchangeRate(
                    rate_date=cls.sales_date2,
                    from_currency=cls.usd,
                    to_currency=cls.usd,
                    rate=1.00,
                ),
            ]
        )
        BookDailySales.objects.bulk_create(
            [
                BookDailySales(
                    book=cls.book1,
                    sale_date=cls.sales_date1,
                    currency=cls.usd,
                    sales=100.00,
                    seller=cls.seller1,
                ),
                BookDailySales(
                    book=cls.book2,
                    sale_date=cls.sales_date1,
                    currency=cls.eur,
                    sales=200.00,
                    seller=cls.seller1,
                ),
                BookDailySales(
                    book=cls.book1,
                    sale_date=cls.sales_date2,
                    currency=cls.usd,
                    sales=50.00,
                    seller=cls.seller2,
                ),
                BookDailySales(
                    book=cls.book2,
                    sale_date=cls.sales_date2,
                    currency=cls.eur,
                    sales=100.00,
                    seller=cls.seller2,
                ),
            ]
        )