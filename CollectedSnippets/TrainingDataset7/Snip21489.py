def test_update_TimeField_using_Value(self):
        Time.objects.create()
        Time.objects.update(time=Value(datetime.time(1), output_field=TimeField()))
        self.assertEqual(Time.objects.get().time, datetime.time(1))