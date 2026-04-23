def test_with_pk_property(self):
        """
        Using the pk property of a model is allowed.
        """
        Thing.objects.update_or_create(pk=1)