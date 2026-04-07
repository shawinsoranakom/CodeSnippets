def test_yaml_bytes_input(self):
        from django.core.serializers.pyyaml import Deserializer as YamlDeserializer

        test_string = """- pk: 1
  model: serializers.author
  fields:
    name: Jane

- pk: 2
  model: serializers.author
  fields:
    name: Joe

- pk: 3
  model: serializers.author
  fields:
    name: John

- pk: 4
  model: serializers.author
  fields:
    name: Smith
"""
        stream = test_string.encode("utf-8")
        deserializer = YamlDeserializer(stream_or_string=stream)

        first_item = next(deserializer)
        second_item = next(deserializer)

        self.assertEqual(first_item.object, self.jane)
        self.assertEqual(second_item.object, self.joe)