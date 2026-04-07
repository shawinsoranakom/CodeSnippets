def test_query_clone(self):
        # Ticket #21643 - Crash when compiling query more than once
        qs = Experiment.objects.filter(end__lt=F("start") + datetime.timedelta(hours=1))
        qs2 = qs.all()
        list(qs)
        list(qs2)