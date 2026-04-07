def test_invalid_values(self):
        msg = "Field 'id' expected a number but got 'abc'."
        with self.assertRaisesMessage(ValueError, msg):
            Annotation.objects.filter(tag="abc")
        with self.assertRaisesMessage(ValueError, msg):
            Annotation.objects.filter(tag__in=[123, "abc"])