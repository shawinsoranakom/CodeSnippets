def test_filter(self):
        with self.assertWarnsMessage(RemovedInDjango70Warning, self.msg):
            self.assertSequenceEqual(
                NullableJSONModel.objects.filter(value=None), [self.obj]
            )