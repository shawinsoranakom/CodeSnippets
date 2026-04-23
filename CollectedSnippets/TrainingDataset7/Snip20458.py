def test_order_by_key(self):
        qs = Author.objects.annotate(attrs=JSONObject(alias=F("alias"))).order_by(
            "attrs__alias"
        )
        self.assertQuerySetEqual(qs, Author.objects.order_by("alias"))