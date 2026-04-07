def test_get_or_create_empty(self):
        """
        If all the attributes on a model have defaults, get_or_create() doesn't
        require any arguments.
        """
        DefaultPerson.objects.get_or_create()