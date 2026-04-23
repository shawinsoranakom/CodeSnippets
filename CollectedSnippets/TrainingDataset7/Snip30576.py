def test_order_by_related_field_transform(self):
        extra_12 = ExtraInfo.objects.create(
            info="extra 12",
            date=DateTimePK.objects.create(date=datetime.datetime(2021, 12, 10)),
        )
        extra_11 = ExtraInfo.objects.create(
            info="extra 11",
            date=DateTimePK.objects.create(date=datetime.datetime(2022, 11, 10)),
        )
        self.assertSequenceEqual(
            ExtraInfo.objects.filter(date__isnull=False).order_by("date__month"),
            [extra_11, extra_12],
        )