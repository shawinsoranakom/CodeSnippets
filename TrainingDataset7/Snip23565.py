def test_proxy_is_returned(self):
        """
        Instances of the proxy should be returned when
        for_concrete_model is False.
        """
        base = ForProxyModelModel()
        base.obj = ProxyRelatedModel.objects.create()
        base.save()

        base = ForProxyModelModel.objects.get(pk=base.pk)
        self.assertIsInstance(base.obj, ProxyRelatedModel)