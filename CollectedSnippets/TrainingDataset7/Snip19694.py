def test_pk_field(self):
        pk = User._meta.get_field("pk")
        self.assertIsInstance(pk, CompositePrimaryKey)
        self.assertIs(User._meta.pk, pk)