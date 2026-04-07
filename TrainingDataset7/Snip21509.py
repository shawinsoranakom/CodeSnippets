def setUpTestData(cls):
        cls.sday = sday = datetime.date(2010, 6, 25)
        cls.stime = stime = datetime.datetime(2010, 6, 25, 12, 15, 30, 747000)
        cls.ex1 = Experiment.objects.create(
            name="Experiment 1",
            assigned=sday,
            completed=sday + datetime.timedelta(2),
            estimated_time=datetime.timedelta(2),
            start=stime,
            end=stime + datetime.timedelta(2),
        )