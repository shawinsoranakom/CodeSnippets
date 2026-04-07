def test_generic_relation_set(self):
        base = ForProxyModelModel()
        base.obj = ConcreteRelatedModel.objects.create()
        base.save()
        newrel = ConcreteRelatedModel.objects.create()

        newrel.bases.set([base])
        newrel = ConcreteRelatedModel.objects.get(pk=newrel.pk)
        self.assertEqual(base, newrel.bases.get())