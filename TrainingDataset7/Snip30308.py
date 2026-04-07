def test_concrete_model(self):
        self.assertEqual(User, UserProxyProxy._meta.concrete_model)