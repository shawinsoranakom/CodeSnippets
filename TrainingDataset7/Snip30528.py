def test_unsupported_ordering_slicing_raises_db_error(self):
        qs1 = Number.objects.all()
        qs2 = Number.objects.all()
        qs3 = Number.objects.all()
        msg = "LIMIT/OFFSET not allowed in subqueries of compound statements"
        with self.assertRaisesMessage(DatabaseError, msg):
            list(qs1.union(qs2[:10]))
        msg = "ORDER BY not allowed in subqueries of compound statements"
        with self.assertRaisesMessage(DatabaseError, msg):
            list(qs1.order_by("id").union(qs2))
        with self.assertRaisesMessage(DatabaseError, msg):
            list(qs1.union(qs2).order_by("id").union(qs3))