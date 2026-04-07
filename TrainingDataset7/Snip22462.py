def test_pickling_foreignobject(self):
        """
        Pickling a ForeignObject does not remove the cached PathInfo values.

        ForeignObject will always keep the path_infos and reverse_path_infos
        attributes within the same process, because of the way
        Field.__reduce__() is used for restoring values.
        """
        foreign_object = Membership._meta.get_field("person")
        # Trigger storage of cached_property into ForeignObjectRel's __dict__
        foreign_object.path_infos
        foreign_object.reverse_path_infos
        self.assertIn("path_infos", foreign_object.__dict__)
        self.assertIn("reverse_path_infos", foreign_object.__dict__)
        foreign_object_restored = pickle.loads(pickle.dumps(foreign_object))
        self.assertIn("path_infos", foreign_object_restored.__dict__)
        self.assertIn("reverse_path_infos", foreign_object_restored.__dict__)