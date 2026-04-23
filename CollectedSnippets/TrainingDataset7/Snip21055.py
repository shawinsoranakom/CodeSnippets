def test_only_and_defer_usage_on_proxy_models(self):
        # Regression for #15790 - only() broken for proxy models
        proxy = Proxy.objects.create(name="proxy", value=42)

        msg = "QuerySet.only() return bogus results with proxy models"
        dp = Proxy.objects.only("other_value").get(pk=proxy.pk)
        self.assertEqual(dp.name, proxy.name, msg=msg)
        self.assertEqual(dp.value, proxy.value, msg=msg)

        # also test things with .defer()
        msg = "QuerySet.defer() return bogus results with proxy models"
        dp = Proxy.objects.defer("name", "text", "value").get(pk=proxy.pk)
        self.assertEqual(dp.name, proxy.name, msg=msg)
        self.assertEqual(dp.value, proxy.value, msg=msg)