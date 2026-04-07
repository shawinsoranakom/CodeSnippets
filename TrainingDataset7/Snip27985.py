def test_deconstruct_custom_encoder_decoder(self):
        field = models.JSONField(encoder=DjangoJSONEncoder, decoder=CustomJSONDecoder)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(kwargs["encoder"], DjangoJSONEncoder)
        self.assertEqual(kwargs["decoder"], CustomJSONDecoder)