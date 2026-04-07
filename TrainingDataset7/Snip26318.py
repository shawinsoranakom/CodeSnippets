def test_fast_add_ignore_conflicts(self):
        """
        A single query is necessary to add auto-created through instances if
        the database backend supports bulk_create(ignore_conflicts) and no
        m2m_changed signals receivers are connected.
        """
        with self.assertNumQueries(1):
            self.a1.publications.add(self.p1, self.p2)