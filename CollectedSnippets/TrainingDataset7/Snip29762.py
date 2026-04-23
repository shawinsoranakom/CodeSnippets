def setUpTestData(cls):
        cls.objs = HStoreModel.objects.bulk_create(
            [
                HStoreModel(field={"a": "b"}),
                HStoreModel(field={"a": "b", "c": "d"}),
                HStoreModel(field={"c": "d"}),
                HStoreModel(field={}),
                HStoreModel(field=None),
                HStoreModel(field={"cat": "TigrOu", "breed": "birman"}),
                HStoreModel(field={"cat": "minou", "breed": "ragdoll"}),
                HStoreModel(field={"cat": "kitty", "breed": "Persian"}),
                HStoreModel(field={"cat": "Kit Kat", "breed": "persian"}),
            ]
        )