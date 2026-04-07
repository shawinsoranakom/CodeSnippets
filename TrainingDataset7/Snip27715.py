def test_serialize_timedelta(self):
        self.assertSerializedEqual(datetime.timedelta())
        self.assertSerializedEqual(datetime.timedelta(minutes=42))