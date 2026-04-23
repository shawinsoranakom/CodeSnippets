def test_serialize_user_json(self):
        users = User.objects.filter(pk=(1, 1))
        result = serializers.serialize("json", users)
        self.assertEqual(
            json.loads(result),
            [
                {
                    "model": "composite_pk.user",
                    "pk": [1, 1],
                    "fields": {
                        "email": "user0001@example.com",
                        "id": 1,
                        "tenant": 1,
                    },
                }
            ],
        )
        self.assert_deserializer(format="json", users=users, serialized_users=result)