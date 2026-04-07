def assert_deserializer(self, format, users, serialized_users):
        deserialized_user = list(serializers.deserialize(format, serialized_users))[0]
        self.assertEqual(deserialized_user.object.email, users[0].email)
        self.assertEqual(deserialized_user.object.id, users[0].id)
        self.assertEqual(deserialized_user.object.tenant, users[0].tenant)
        self.assertEqual(deserialized_user.object.pk, users[0].pk)