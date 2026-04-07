def test_model_pickle_m2m(self):
        """
        Test intentionally the automatically created through model.
        """
        m1 = M2MModel.objects.create()
        g1 = Group.objects.create(name="foof")
        m1.groups.add(g1)
        m2m_through = M2MModel._meta.get_field("groups").remote_field.through
        original = m2m_through.objects.get()
        dumped = pickle.dumps(original)
        reloaded = pickle.loads(dumped)
        self.assertEqual(original, reloaded)