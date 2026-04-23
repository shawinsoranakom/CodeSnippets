def test_binaryfield(self):
        BinaryFieldModel.objects.create(data=b"binary data")
        self.assert_pickles(BinaryFieldModel.objects.all())