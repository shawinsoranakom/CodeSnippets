def test_proxy_delete(self):
        """
        Proxy objects can be deleted
        """
        User.objects.create(name="Bruce")
        u2 = UserProxy.objects.create(name="George")

        resp = [u.name for u in UserProxy.objects.all()]
        self.assertEqual(resp, ["Bruce", "George"])

        u2.delete()

        resp = [u.name for u in UserProxy.objects.all()]
        self.assertEqual(resp, ["Bruce"])