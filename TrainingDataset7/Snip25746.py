def setUpTestData(cls):
        cls.p1 = Product.objects.create(name="Product1", qty_target=10)
        Stock.objects.create(product=cls.p1, qty_available=5)
        Stock.objects.create(product=cls.p1, qty_available=6)
        cls.p2 = Product.objects.create(name="Product2", qty_target=10)
        Stock.objects.create(product=cls.p2, qty_available=5)
        Stock.objects.create(product=cls.p2, qty_available=5)
        cls.p3 = Product.objects.create(name="Product3", qty_target=10)
        Stock.objects.create(product=cls.p3, qty_available=5)
        Stock.objects.create(product=cls.p3, qty_available=4)
        cls.queryset = Product.objects.annotate(
            qty_available_sum=Sum("stock__qty_available"),
        ).annotate(qty_needed=F("qty_target") - F("qty_available_sum"))