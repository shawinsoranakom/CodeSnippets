def test_annotation_q_filter(self):
        qs = NullableJSONModel.objects.annotate(
            has_empty_data=Q(value__isnull=True) | Q(value=None)
        ).filter(has_empty_data=True)
        with self.assertWarnsMessage(RemovedInDjango70Warning, self.msg):
            self.assertSequenceEqual(qs, [self.obj])