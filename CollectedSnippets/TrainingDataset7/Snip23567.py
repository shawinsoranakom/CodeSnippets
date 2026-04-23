def test_query_proxy(self):
        base = ForProxyModelModel()
        base.obj = rel = ProxyRelatedModel.objects.create()
        base.save()

        self.assertEqual(rel, ProxyRelatedModel.objects.get(bases__id=base.id))