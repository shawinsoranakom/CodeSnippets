def test_error_messages(self):
        error_messages = {
            "invalid_page": "Wrong page number",
            "min_page": "Too small",
            "no_results": "There is nothing here",
        }
        paginator = Paginator([1, 2, 3], 2, error_messages=error_messages)
        msg = "Wrong page number"
        with self.assertRaisesMessage(PageNotAnInteger, msg):
            paginator.validate_number(1.2)
        msg = "Too small"
        with self.assertRaisesMessage(EmptyPage, msg):
            paginator.validate_number(-1)
        msg = "There is nothing here"
        with self.assertRaisesMessage(EmptyPage, msg):
            paginator.validate_number(3)

        error_messages = {"min_page": "Too small"}
        paginator = Paginator([1, 2, 3], 2, error_messages=error_messages)
        # Custom message.
        msg = "Too small"
        with self.assertRaisesMessage(EmptyPage, msg):
            paginator.validate_number(-1)
        # Default message.
        msg = "That page contains no results"
        with self.assertRaisesMessage(EmptyPage, msg):
            paginator.validate_number(3)