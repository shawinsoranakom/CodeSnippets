def test_filter_by_related_field_nested_transforms(self):
        extra = ExtraInfo.objects.create(info=" extra")
        a5 = Author.objects.create(name="a5", num=5005, extra=extra)
        info_field = ExtraInfo._meta.get_field("info")
        with register_lookup(info_field, Length), register_lookup(CharField, LTrim):
            self.assertSequenceEqual(
                Author.objects.filter(extra__info__ltrim__length=5), [a5]
            )