def test_force_update_on_proxy_model(self):
        a = ProxyCounter(name="count", value=1)
        a.save()
        a.save(force_update=True)