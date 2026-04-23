def test_get_previous_by_field(self):
        stamp_1 = TimeStamped.objects.create(id=1)
        stamp_2 = TimeStamped(id=2)
        msg = "get_next/get_previous cannot be used on unsaved objects."
        with self.assertRaisesMessage(ValueError, msg):
            stamp_2.get_previous_by_created()
        stamp_2.save()
        self.assertEqual(stamp_2.get_previous_by_created(), stamp_1)