def test_custom_encoder(self):
        class ScoreDecimal(models.Model):
            score = models.DecimalField()

        class CustomJSONEncoder(json.JSONEncoder):
            def default(self, o):
                if isinstance(o, decimal.Decimal):
                    return str(o)
                return super().default(o)

        s = serializers.json.Serializer()
        json_data = s.serialize(
            [ScoreDecimal(score=decimal.Decimal(1.0))], cls=CustomJSONEncoder
        )
        self.assertIn('"fields": {"score": "1"}', json_data)