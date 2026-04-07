def test_order_by_nested_key(self):
        qs = Author.objects.annotate(arr=JSONArray(JSONArray(F("alias")))).order_by(
            "-arr__0__0"
        )
        self.assertQuerySetEqual(qs, Author.objects.order_by("-alias"))