def test_serialize_to_stream(self):
        obj = ComplexModel(field1="first", field2="second", field3="third")
        obj.save_base(raw=True)

        # Serialize the test database to a stream
        for stream in (StringIO(), HttpResponse()):
            serializers.serialize(self.serializer_name, [obj], indent=2, stream=stream)

            # Serialize normally for a comparison
            string_data = serializers.serialize(self.serializer_name, [obj], indent=2)

            # The two are the same
            if isinstance(stream, StringIO):
                self.assertEqual(string_data, stream.getvalue())
            else:
                self.assertEqual(string_data, stream.text)