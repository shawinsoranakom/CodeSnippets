def test_pickle_prefetch_related_with_m2m_and_objects_deletion(self):
        """
        #24831 -- Cached properties on ManyToOneRel created in
        QuerySet.delete() caused subsequent QuerySet pickling to fail.
        """
        g = Group.objects.create(name="foo")
        m2m = M2MModel.objects.create()
        m2m.groups.add(g)
        Group.objects.all().delete()

        m2ms = M2MModel.objects.prefetch_related("groups")
        m2ms = pickle.loads(pickle.dumps(m2ms))
        self.assertSequenceEqual(m2ms, [m2m])