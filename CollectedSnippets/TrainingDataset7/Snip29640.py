def test_dumping(self):
        instance = IntegerArrayModel(field=[1, 2, None])
        data = serializers.serialize("json", [instance])
        self.assertEqual(json.loads(data), json.loads(self.test_data))