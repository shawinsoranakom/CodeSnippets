def test_custom_encoder(self):
        field = models.JSONField(encoder=DjangoJSONEncoder)
        value = uuid.UUID("{d85e2076-b67c-4ee7-8c3a-2bf5a2cc2475}")
        field.clean({"uuid": value}, None)