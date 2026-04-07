def test_copy_removes_direct_cached_values(self):
        """
        Shallow copying a ForeignObject (or a ForeignObjectRel) removes the
        object's direct cached PathInfo values.
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
        # because no __copy__() method exists, so __reduce_ex__() is used.
        remote_field_copy = copy.copy(foreign_object.remote_field)
        self.assertNotIn("path_infos", remote_field_copy.__dict__)
        # Cached values are removed via __copy__() on ForeignObject for
        # consistency of behavior.
        foreign_object_copy = copy.copy(foreign_object)
        self.assertNotIn("path_infos", foreign_object_copy.__dict__)
        self.assertNotIn("reverse_path_infos", foreign_object_copy.__dict__)
        # ForeignObjectRel's remains because it's part of a shallow copy.
        self.assertIn("path_infos", foreign_object_copy.remote_field.__dict__)