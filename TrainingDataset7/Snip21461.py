def test_multiple_query_compilation(self):
        # Ticket #21643
        queryset = Experiment.objects.filter(
            end__lt=F("start") + datetime.timedelta(hours=1)
        )
        q1 = str(queryset.query)
        q2 = str(queryset.query)
        self.assertEqual(q1, q2)