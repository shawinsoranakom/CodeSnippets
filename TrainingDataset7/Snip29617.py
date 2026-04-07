def setUpTestData(cls):
        now = timezone.now()
        cls.datetimes = [now]
        cls.dates = [now.date()]
        cls.times = [now.time()]
        cls.objs = [
            DateTimeArrayModel.objects.create(
                datetimes=cls.datetimes, dates=cls.dates, times=cls.times
            ),
        ]