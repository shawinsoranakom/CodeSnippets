def test_nulls_false(self):
        msg = "nulls_first and nulls_last values must be True or None."
        with self.assertRaisesMessage(ValueError, msg):
            OrderBy(F("field"), nulls_first=False)
        with self.assertRaisesMessage(ValueError, msg):
            OrderBy(F("field"), nulls_last=False)
        with self.assertRaisesMessage(ValueError, msg):
            F("field").asc(nulls_first=False)
        with self.assertRaisesMessage(ValueError, msg):
            F("field").desc(nulls_last=False)