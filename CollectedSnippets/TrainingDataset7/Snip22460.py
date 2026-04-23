def test_deepcopy_removes_cached_values(self):
        """
        Deep copying a ForeignObject removes the object's cached PathInfo
        values, including those of the related ForeignObjectRel.
        """
        foreign_object = Membership._meta.get_field("person")
        # Trigger storage of cached_property into ForeignObject's __dict__.
        foreign_object.path_infos
        foreign_object.reverse_path_infos
        # The ForeignObjectRel doesn't have reverse_path_infos.
        foreign_object.remote_field.path_infos
        self.assertIn("path_infos", foreign_object.__dict__)
        self.assertIn("reverse_path_infos", foreign_object.__dict__)
        self.assertIn("path_infos", foreign_object.remote_field.__dict__)
        # Cached value is removed via __getstate__() on ForeignObjectRel
        # because no __deepcopy__() method exists, so __reduce_ex__() is used.
        remote_field_copy = copy.deepcopy(foreign_object.remote_field)
        self.assertNotIn("path_infos", remote_field_copy.__dict__)
        # Field.__deepcopy__() internally uses __copy__() on both the
        # ForeignObject and ForeignObjectRel, so all cached values are removed.
        foreign_object_copy = copy.deepcopy(foreign_object)
        self.assertNotIn("path_infos", foreign_object_copy.__dict__)
        self.assertNotIn("reverse_path_infos", foreign_object_copy.__dict__)
        self.assertNotIn("path_infos", foreign_object_copy.remote_field.__dict__)