def test_overflow_translation(self):
        msg = "Le nombre de jours doit être entre {min_days} et {max_days}.".format(
            min_days=datetime.timedelta.min.days,
            max_days=datetime.timedelta.max.days,
        )
        with translation.override("fr"):
            with self.assertRaisesMessage(ValidationError, msg):
                DurationField().clean("1000000000 00:00:00")