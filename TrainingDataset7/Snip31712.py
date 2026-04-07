def test_no_indentation(self):
        s = serializers.jsonl.Serializer()
        json_data = s.serialize([Score(score=5.0), Score(score=6.0)], indent=2)
        for line in json_data.splitlines():
            self.assertIsNone(re.search(r".+,\s*$", line))