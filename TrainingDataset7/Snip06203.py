def _check_encode_args(self, password, salt):
        if password is None:
            raise TypeError("password must be provided.")
        if not salt or "$" in force_str(salt):  # salt can be str or bytes.
            raise ValueError("salt must be provided and cannot contain $.")