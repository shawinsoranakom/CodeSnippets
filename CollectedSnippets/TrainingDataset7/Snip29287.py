def test_primary_key_to_field_filter(self):
        target = Target.objects.create(name="foo")
        pointer = ToFieldPointer.objects.create(target=target)
        self.assertSequenceEqual(
            ToFieldPointer.objects.filter(target=target), [pointer]
        )
        self.assertSequenceEqual(
            ToFieldPointer.objects.filter(pk__exact=pointer), [pointer]
        )