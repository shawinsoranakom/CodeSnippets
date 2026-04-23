def to_python(self, value):
        """
        Explicitly check for the string 'True' and 'False', which is what a
        hidden field will submit for True and False, for 'true' and 'false',
        which are likely to be returned by JavaScript serializations of forms,
        and for '1' and '0', which is what a RadioField will submit. Unlike
        the Booleanfield, this field must check for True because it doesn't
        use the bool() function.
        """
        if value in (True, "True", "true", "1"):
            return True
        elif value in (False, "False", "false", "0"):
            return False
        else:
            return None