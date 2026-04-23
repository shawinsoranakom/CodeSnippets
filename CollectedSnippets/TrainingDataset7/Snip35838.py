def test_reverse_outer_in_response_middleware(self):
        """
        Test reversing an URL from the *default* URLconf from inside
        a response middleware.
        """
        msg = (
            "Reverse for 'outer' not found. 'outer' is not a valid view "
            "function or pattern name."
        )
        with self.assertRaisesMessage(NoReverseMatch, msg):
            self.client.get("/second_test/")