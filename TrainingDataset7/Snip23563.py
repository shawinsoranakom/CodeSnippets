def test_default_behavior(self):
        """
        The default for for_concrete_model should be True
        """
        base = ForConcreteModelModel()
        base.obj = rel = ProxyRelatedModel.objects.create()
        base.save()

        base = ForConcreteModelModel.objects.get(pk=base.pk)
        rel = ConcreteRelatedModel.objects.get(pk=rel.pk)
        self.assertEqual(base.obj, rel)