def test_error_raised_on_filter_with_dictionary(self):
        with self.assertRaisesMessage(FieldError, "Cannot parse keyword query as dict"):
            Note.objects.filter({"note": "n1", "misc": "foo"})