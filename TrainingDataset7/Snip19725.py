def test_serialize_datetime(self):
        result = serializers.serialize("json", TimeStamped.objects.all())
        self.assertEqual(
            json.loads(result),
            [
                {
                    "model": "composite_pk.timestamped",
                    "pk": [1, "2022-01-12T05:55:14.956"],
                    "fields": {
                        "id": 1,
                        "created": "2022-01-12T05:55:14.956",
                        "text": "",
                    },
                },
            ],
        )