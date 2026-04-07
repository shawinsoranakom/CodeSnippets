def test_filter_bytearray(self):
        dm = DataModel.objects.create(data=self.binary_data)
        DataModel.objects.create(data=b"\xef\xbb\xbf")
        self.assertSequenceEqual(
            DataModel.objects.filter(data=bytearray(self.binary_data)), [dm]
        )