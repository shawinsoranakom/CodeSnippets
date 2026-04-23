def test_query(self):
        base = ForProxyModelModel()
        base.obj = rel = ConcreteRelatedModel.objects.create()
        base.save()

        self.assertEqual(rel, ConcreteRelatedModel.objects.get(bases__id=base.id))