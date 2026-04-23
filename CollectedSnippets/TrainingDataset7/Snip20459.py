def test_order_by_nested_key(self):
        qs = Author.objects.annotate(
            attrs=JSONObject(nested=JSONObject(alias=F("alias")))
        ).order_by("-attrs__nested__alias")
        self.assertQuerySetEqual(qs, Author.objects.order_by("-alias"))