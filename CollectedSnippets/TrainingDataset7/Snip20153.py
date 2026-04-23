def test_datetime_output_field(self):
        with register_lookup(models.PositiveIntegerField, DateTimeTransform):
            ut = MySQLUnixTimestamp.objects.create(timestamp=time.time())
            y2k = timezone.make_aware(datetime(2000, 1, 1))
            self.assertSequenceEqual(
                MySQLUnixTimestamp.objects.filter(timestamp__as_datetime__gt=y2k), [ut]
            )