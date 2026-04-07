def test_inherited_ordering_pk_desc(self):
        p1 = Parent.objects.create(first_name="Joe", email="joe@email.com")
        p2 = Parent.objects.create(first_name="Jon", email="jon@email.com")
        expected_order_by_sql = "ORDER BY %s.%s DESC" % (
            connection.ops.quote_name(Parent._meta.db_table),
            connection.ops.quote_name(Parent._meta.get_field("grandparent_ptr").column),
        )
        qs = Parent.objects.all()
        self.assertSequenceEqual(qs, [p2, p1])
        self.assertIn(expected_order_by_sql, str(qs.query))