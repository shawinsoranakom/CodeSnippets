def test_serialize_user_jsonl(self):
        users = User.objects.filter(pk=(1, 2))
        result = serializers.serialize("jsonl", users)
        self.assertEqual(
            json.loads(result),
            {
                "model": "composite_pk.user",
                "pk": [1, 2],
                "fields": {
                    "email": "user0002@example.com",
                    "id": 2,
                    "tenant": 1,
                },
            },
        )
        self.assert_deserializer(format="jsonl", users=users, serialized_users=result)