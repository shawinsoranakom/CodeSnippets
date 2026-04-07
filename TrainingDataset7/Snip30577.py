def test_filter_by_related_field_transform(self):
        extra_old = ExtraInfo.objects.create(
            info="extra 12",
            date=DateTimePK.objects.create(date=datetime.datetime(2020, 12, 10)),
        )
        ExtraInfo.objects.create(info="extra 11", date=DateTimePK.objects.create())
        a5 = Author.objects.create(name="a5", num=5005, extra=extra_old)

        fk_field = ExtraInfo._meta.get_field("date")
        with register_lookup(fk_field, ExtractYear):
            self.assertSequenceEqual(
                ExtraInfo.objects.filter(date__year=2020),
                [extra_old],
            )
            self.assertSequenceEqual(
                Author.objects.filter(extra__date__year=2020), [a5]
            )