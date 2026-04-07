def test_proxy_for_model(self):
        self.assertEqual(UserProxy, UserProxyProxy._meta.proxy_for_model)