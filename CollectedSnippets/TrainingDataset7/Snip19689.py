def test_pk_updated_if_field_updated(self):
        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(user.pk, (self.tenant.id, self.user.id))
        self.assertIs(user._is_pk_set(), True)
        user.tenant_id = 9831
        self.assertEqual(user.pk, (9831, self.user.id))
        self.assertIs(user._is_pk_set(), True)
        user.id = 4321
        self.assertEqual(user.pk, (9831, 4321))
        self.assertIs(user._is_pk_set(), True)
        user.pk = (9132, 3521)
        self.assertEqual(user.tenant_id, 9132)
        self.assertEqual(user.id, 3521)
        self.assertIs(user._is_pk_set(), True)
        user.id = None
        self.assertEqual(user.pk, (9132, None))
        self.assertEqual(user.tenant_id, 9132)
        self.assertIsNone(user.id)
        self.assertIs(user._is_pk_set(), False)