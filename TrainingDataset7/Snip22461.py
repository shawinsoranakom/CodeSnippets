def test_pickling_foreignobjectrel(self):
        """
        Pickling a ForeignObjectRel removes the path_infos attribute.

        ForeignObjectRel implements __getstate__(), so copy and pickle modules
        both use that, but ForeignObject implements __reduce__() and __copy__()
        separately, so doesn't share the same behavior.
        """
        foreign_object_rel = Membership._meta.get_field("person").remote_field
        # Trigger storage of cached_property into ForeignObjectRel's __dict__.
        foreign_object_rel.path_infos
        self.assertIn("path_infos", foreign_object_rel.__dict__)
        foreign_object_rel_restored = pickle.loads(pickle.dumps(foreign_object_rel))
        self.assertNotIn("path_infos", foreign_object_rel_restored.__dict__)