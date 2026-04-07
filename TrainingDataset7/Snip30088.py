def test_hstore_values(self):
        oids, array_oids = get_hstore_oids(connection.alias)
        self.assertOIDs(oids)
        self.assertOIDs(array_oids)