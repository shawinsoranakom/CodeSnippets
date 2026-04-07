def test_dumpdata_proxy_without_concrete(self):
        """
        A warning is displayed if a proxy model is dumped without its concrete
        parent.
        """
        ProxySpy.objects.create(name="Paul")
        msg = "fixtures.ProxySpy is a proxy model and won't be serialized."
        with self.assertWarnsMessage(ProxyModelWarning, msg):
            self._dumpdata_assert(["fixtures.ProxySpy"], "[]")