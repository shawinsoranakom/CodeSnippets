def test_defer_with_select_related(self):
        item1 = Item.objects.create(name="first", value=47)
        item2 = Item.objects.create(name="second", value=42)
        simple = SimpleItem.objects.create(name="simple", value="23")
        ItemAndSimpleItem.objects.create(item=item1, simple=simple)

        obj = ItemAndSimpleItem.objects.defer("item").select_related("simple").get()
        self.assertEqual(obj.item, item1)
        self.assertEqual(obj.item_id, item1.id)

        obj.item = item2
        obj.save()

        obj = ItemAndSimpleItem.objects.defer("item").select_related("simple").get()
        self.assertEqual(obj.item, item2)
        self.assertEqual(obj.item_id, item2.id)