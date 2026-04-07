def test_works_normally(self):
        """
        When for_concrete_model is False, we should still be able to get
        an instance of the concrete class.
        """
        base = ForProxyModelModel()
        base.obj = rel = ConcreteRelatedModel.objects.create()
        base.save()

        base = ForProxyModelModel.objects.get(pk=base.pk)
        self.assertEqual(base.obj, rel)