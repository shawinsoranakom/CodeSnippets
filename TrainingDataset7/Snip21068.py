def setUpTestData(cls):
        cls.item_pk = Item.objects.create(value=1).pk