def test_clean_false(self):
        """
        If the ``clean`` method on a non-required FileField receives False as
        the data (meaning clear the field value), it returns False, regardless
        of the value of ``initial``.
        """
        f = forms.FileField(required=False)
        self.assertIs(f.clean(False), False)
        self.assertIs(f.clean(False, "initial"), False)