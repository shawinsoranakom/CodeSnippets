def test_extract_second_func_no_fractional(self):
        start_datetime = datetime.datetime(2015, 6, 15, 14, 30, 50, 321)
        end_datetime = datetime.datetime(2016, 6, 15, 14, 30, 50, 783)
        if settings.USE_TZ:
            start_datetime = timezone.make_aware(start_datetime)
            end_datetime = timezone.make_aware(end_datetime)
        obj = self.create_model(start_datetime, end_datetime)
        self.assertSequenceEqual(
            DTModel.objects.filter(start_datetime__second=F("end_datetime__second")),
            [obj],
        )
        self.assertSequenceEqual(
            DTModel.objects.filter(start_time__second=F("end_time__second")),
            [obj],
        )