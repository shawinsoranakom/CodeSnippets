def test_exact(self):
        self.assertSequenceEqual(
            DurationModel.objects.filter(field=datetime.timedelta(days=1)),
            [self.objs[0]],
        )