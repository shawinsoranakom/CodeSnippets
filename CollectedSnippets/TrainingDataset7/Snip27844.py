def test_dumping(self):
        instance = DurationModel(field=datetime.timedelta(days=1, hours=1))
        data = serializers.serialize("json", [instance])
        self.assertEqual(json.loads(data), json.loads(self.test_data))