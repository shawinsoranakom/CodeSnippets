def test_serialize_post_uuid(self):
        posts = Post.objects.filter(pk=(2, "11111111-1111-1111-1111-111111111111"))
        result = serializers.serialize("json", posts)
        self.assertEqual(
            json.loads(result),
            [
                {
                    "model": "composite_pk.post",
                    "pk": [2, "11111111-1111-1111-1111-111111111111"],
                    "fields": {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "tenant": 2,
                    },
                },
            ],
        )