def test_proxy_model_defer_with_select_related(self):
        # Regression for #22050
        item = Item.objects.create(name="first", value=47)
        RelatedItem.objects.create(item=item)
        # Defer fields with only()
        obj = ProxyRelated.objects.select_related().only("item__name")[0]
        with self.assertNumQueries(0):
            self.assertEqual(obj.item.name, "first")
        with self.assertNumQueries(1):
            self.assertEqual(obj.item.value, 47)