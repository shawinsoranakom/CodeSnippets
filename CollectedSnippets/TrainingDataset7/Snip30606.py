def test_ticket7813(self):
        # We should also be able to pickle things that use select_related().
        # The only tricky thing here is to ensure that we do the related
        # selections properly after unpickling.
        qs = Item.objects.select_related()
        query = qs.query.get_compiler(qs.db).as_sql()[0]
        query2 = pickle.loads(pickle.dumps(qs.query))
        self.assertEqual(query2.get_compiler(qs.db).as_sql()[0], query)