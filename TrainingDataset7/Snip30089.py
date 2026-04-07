def test_citext_values(self):
        oids, citext_oids = get_citext_oids(connection.alias)
        self.assertOIDs(oids)
        self.assertOIDs(citext_oids)