def test_serialize_generic_alias_complex_args(self):
        self.assertSerializedEqual(dict[str, models.Manager])