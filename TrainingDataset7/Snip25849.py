def test_exact_booleanfield(self):
        # MySQL ignores indexes with boolean fields unless they're compared
        # directly to a boolean value.
        product = Product.objects.create(name="Paper", qty_target=5000)
        Stock.objects.create(product=product, short=False, qty_available=5100)
        stock_1 = Stock.objects.create(product=product, short=True, qty_available=180)
        qs = Stock.objects.filter(short=True)
        self.assertSequenceEqual(qs, [stock_1])
        self.assertIn(
            "%s = True" % connection.ops.quote_name("short"),
            str(qs.query),
        )