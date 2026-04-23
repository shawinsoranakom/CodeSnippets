def test_serialize_user_xml(self):
        users = User.objects.filter(pk=(1, 1))
        result = serializers.serialize("xml", users)
        self.assertIn('<object model="composite_pk.user" pk=\'["1", "1"]\'>', result)
        self.assert_deserializer(format="xml", users=users, serialized_users=result)