def test_case_when(self):
        qs = NullableJSONModel.objects.annotate(
            has_json_null=Case(When(value=None, then=Value(True)), default=Value(False))
        ).filter(has_json_null=True)
        with self.assertWarnsMessage(RemovedInDjango70Warning, self.msg):
            self.assertSequenceEqual(qs, [self.obj])