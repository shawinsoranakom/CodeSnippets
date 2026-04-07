def test_multivalue_dict_key_error(self):
        """
        #21098 -- Sensitive POST parameters cannot be seen in the
        error reports for if request.POST['nonexistent_key'] throws an error.
        """
        with self.settings(DEBUG=True):
            self.verify_unsafe_response(multivalue_dict_key_error)
            self.verify_unsafe_email(multivalue_dict_key_error)

        with self.settings(DEBUG=False):
            self.verify_safe_response(multivalue_dict_key_error)
            self.verify_safe_email(multivalue_dict_key_error)