def test_serialize_user_python(self):
        users = User.objects.filter(pk=(2, 4))
        result = serializers.serialize("python", users)
        self.assertEqual(
            result,
            [
                {
                    "model": "composite_pk.user",
                    "pk": [2, 4],
                    "fields": {
                        "email": "user0004@example.com",
                        "id": 4,
                        "tenant": 2,
                    },
                },
            ],
        )
        self.assert_deserializer(format="python", users=users, serialized_users=result)