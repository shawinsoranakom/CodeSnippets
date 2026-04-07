def test_proxied_model_duplicate_queries(self):
        """
        #25685 - Deleting instances of a model with existing proxy
        classes should not issue multiple queries during cascade
        deletion of referring models.
        """
        avatar = Avatar.objects.create()
        # One query for the Avatar table and a second for the User one.
        with self.assertNumQueries(2):
            avatar.delete()