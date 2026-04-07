def test_datetimes_invalid_field(self):
        # An error should be raised when QuerySet.datetimes() is passed the
        # wrong type of field.
        msg = "'name' isn't a DateField, TimeField, or DateTimeField."
        with self.assertRaisesMessage(TypeError, msg):
            Item.objects.datetimes("name", "month")