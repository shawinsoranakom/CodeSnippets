def test_get_or_create_with_pk_property(self):
        """
        Using the pk property of a model is allowed.
        """
        Thing.objects.get_or_create(pk=1)