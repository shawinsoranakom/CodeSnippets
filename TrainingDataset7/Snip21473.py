def test_invalid_operator(self):
        with self.assertRaises(DatabaseError):
            list(Experiment.objects.filter(start=F("start") * datetime.timedelta(0)))