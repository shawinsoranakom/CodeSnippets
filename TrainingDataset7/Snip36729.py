def test_is_aware(self):
        self.assertTrue(
            timezone.is_aware(datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT))
        )
        self.assertFalse(timezone.is_aware(datetime.datetime(2011, 9, 1, 13, 20, 30)))