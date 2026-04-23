def test_gt(self):
        self.assertCountEqual(
            DurationModel.objects.filter(field__gt=datetime.timedelta(days=0)),
            [self.objs[0], self.objs[1]],
        )