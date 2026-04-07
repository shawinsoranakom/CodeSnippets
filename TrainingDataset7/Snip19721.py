def test_serialize_user_yaml(self):
        users = User.objects.filter(pk=(2, 3))
        result = serializers.serialize("yaml", users)
        self.assertEqual(
            yaml.safe_load(result),
            [
                {
                    "model": "composite_pk.user",
                    "pk": [2, 3],
                    "fields": {
                        "email": "user0003@example.com",
                        "id": 3,
                        "tenant": 2,
                    },
                },
            ],
        )
        self.assert_deserializer(format="yaml", users=users, serialized_users=result)