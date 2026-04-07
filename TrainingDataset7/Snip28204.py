def test_field_instance_is_picklable(self):
        """Field instances can be pickled."""
        field = models.Field(max_length=100, default="a string")
        # Must be picklable with this cached property populated (#28188).
        field._get_default
        pickle.dumps(field)