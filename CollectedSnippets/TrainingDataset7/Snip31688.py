def test_json_bytes_input(self):
        test_string = json.dumps(self.object_list)
        stream = test_string.encode("utf-8")
        deserializer = JsonDeserializer(stream_or_string=stream)

        first_item = next(deserializer)
        second_item = next(deserializer)

        self.assertEqual(first_item.object, self.jane)
        self.assertEqual(second_item.object, self.joe)