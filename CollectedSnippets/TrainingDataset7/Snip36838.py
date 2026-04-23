def test_max_length_validator_message(self):
        v = MaxLengthValidator(
            16, message='"%(value)s" has more than %(limit_value)d characters.'
        )
        with self.assertRaisesMessage(
            ValidationError, '"djangoproject.com" has more than 16 characters.'
        ):
            v("djangoproject.com")