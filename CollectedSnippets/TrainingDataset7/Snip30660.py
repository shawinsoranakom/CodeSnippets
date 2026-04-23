def test_filter_reverse_non_integer_pk(self):
        date_obj = DateTimePK.objects.create()
        extra_obj = ExtraInfo.objects.create(info="extra", date=date_obj)
        self.assertEqual(
            DateTimePK.objects.filter(extrainfo=extra_obj).get(),
            date_obj,
        )