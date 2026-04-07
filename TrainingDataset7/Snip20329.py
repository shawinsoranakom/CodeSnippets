def test_cast_from_db_datetime_to_date_group_by(self):
        author = Author.objects.create(name="John Smith", age=45)
        dt_value = datetime.datetime(2018, 9, 28, 12, 42, 10, 234567)
        Fan.objects.create(name="Margaret", age=50, author=author, fan_since=dt_value)
        fans = (
            Fan.objects.values("author")
            .annotate(
                fan_for_day=Cast("fan_since", models.DateField()),
                fans=models.Count("*"),
            )
            .values()
        )
        self.assertEqual(fans[0]["fan_for_day"], datetime.date(2018, 9, 28))
        self.assertEqual(fans[0]["fans"], 1)