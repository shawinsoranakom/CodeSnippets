def test_invalid_status_code(self):
        must_be_integer = "HTTP status code must be an integer."
        must_be_integer_in_range = (
            "HTTP status code must be an integer from 100 to 599."
        )
        with self.assertRaisesMessage(TypeError, must_be_integer):
            HttpResponse(status=object())
        with self.assertRaisesMessage(TypeError, must_be_integer):
            HttpResponse(status="J'attendrai")
        with self.assertRaisesMessage(ValueError, must_be_integer_in_range):
            HttpResponse(status=99)
        with self.assertRaisesMessage(ValueError, must_be_integer_in_range):
            HttpResponse(status=600)