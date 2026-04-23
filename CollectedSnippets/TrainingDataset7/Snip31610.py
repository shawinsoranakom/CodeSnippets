def test_reverse_related_validation(self):
        fields = "userprofile, userstat"

        with self.assertRaisesMessage(
            FieldError, self.invalid_error % ("foobar", fields)
        ):
            list(User.objects.select_related("foobar"))

        with self.assertRaisesMessage(
            FieldError, self.non_relational_error % ("username", fields)
        ):
            list(User.objects.select_related("username"))