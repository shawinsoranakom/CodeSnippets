def test_xml_serialization(self):
        test_xml_data = (
            '<django-objects version="1.0">'
            '<object model="model_fields.nullablejsonmodel">'
            '<field name="value" type="JSONField">%s'
            "</field></object></django-objects>"
        )
        for value, serialized in self.test_values:
            with self.subTest(value=value):
                instance = NullableJSONModel(value=value)
                data = serializers.serialize("xml", [instance], fields=["value"])
                self.assertXMLEqual(data, test_xml_data % serialized)
                new_instance = list(serializers.deserialize("xml", data))[0].object
                self.assertEqual(new_instance.value, instance.value)