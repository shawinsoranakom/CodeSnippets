def test_lookup_rhs(self):
        product = Product.objects.create(name="GME", qty_target=5000)
        stock_1 = Stock.objects.create(product=product, short=True, qty_available=180)
        stock_2 = Stock.objects.create(product=product, short=False, qty_available=5100)
        Stock.objects.create(product=product, short=False, qty_available=4000)
        self.assertCountEqual(
            Stock.objects.filter(short=Q(qty_available__lt=F("product__qty_target"))),
            [stock_1, stock_2],
        )
        self.assertCountEqual(
            Stock.objects.filter(
                short=ExpressionWrapper(
                    Q(qty_available__lt=F("product__qty_target")),
                    output_field=BooleanField(),
                )
            ),
            [stock_1, stock_2],
        )