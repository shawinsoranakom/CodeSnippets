def test_order_by_key(self):
        qs = Author.objects.annotate(arr=JSONArray(F("alias"))).order_by("arr__0")
        self.assertQuerySetEqual(qs, Author.objects.order_by("alias"))