def test_indentation_whitespace(self):
        s = serializers.json.Serializer()
        json_data = s.serialize([Score(score=5.0), Score(score=6.0)], indent=2)
        for line in json_data.splitlines():
            if re.search(r".+,\s*$", line):
                self.assertEqual(line, line.rstrip())