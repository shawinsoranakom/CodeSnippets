def test_annotation_values(self):
        qs = Happening.objects.values("name").annotate(latest_time=models.Max("when"))
        reloaded = Happening.objects.all()
        reloaded.query = pickle.loads(pickle.dumps(qs.query))
        self.assertEqual(
            reloaded.get(),
            {"name": "test", "latest_time": self.happening.when},
        )