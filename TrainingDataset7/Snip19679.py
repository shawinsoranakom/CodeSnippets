def test_update_token_by_tenant_name(self):
        result = Token.objects.filter(tenant__name="A").update(secret="bar")

        self.assertEqual(result, 2)
        token_1 = Token.objects.get(pk=self.token_1.pk)
        self.assertEqual(token_1.secret, "bar")
        token_3 = Token.objects.get(pk=self.token_3.pk)
        self.assertEqual(token_3.secret, "bar")