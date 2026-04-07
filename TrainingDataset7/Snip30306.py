def test_user_proxy_models(self):
        User.objects.create(name="Bruce")

        resp = [u.name for u in User.objects.all()]
        self.assertEqual(resp, ["Bruce"])

        resp = [u.name for u in UserProxy.objects.all()]
        self.assertEqual(resp, ["Bruce"])

        resp = [u.name for u in UserProxyProxy.objects.all()]
        self.assertEqual(resp, ["Bruce"])

        self.assertEqual([u.name for u in MultiUserProxy.objects.all()], ["Bruce"])