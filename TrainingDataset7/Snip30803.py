def test_no_extra_params(self):
        """
        Can create an instance of a model with only the PK field (#17056)."
        """
        DumbCategory.objects.create()