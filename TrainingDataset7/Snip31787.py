def test_stream_class(self):
        class File:
            def __init__(self):
                self.lines = []

            def write(self, line):
                self.lines.append(line)

            def getvalue(self):
                return "".join(self.lines)

        class Serializer(serializers.json.Serializer):
            stream_class = File

        serializer = Serializer()
        data = serializer.serialize([Score(id=1, score=3.4)])
        self.assertIs(serializer.stream_class, File)
        self.assertIsInstance(serializer.stream, File)
        self.assertEqual(
            data,
            '[{"model": "serializers.score", "pk": 1, "fields": {"score": 3.4}}]\n',
        )