def test_updating_non_conditional_field(self):
        msg = "Cannot negate non-conditional expressions."
        with self.assertRaisesMessage(TypeError, msg):
            DataPoint.objects.update(is_active=~F("name"))