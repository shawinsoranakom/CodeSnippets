def test_foreign_key(self):
        query = Query(Item)
        msg = "Joined field references are not permitted in this query"
        with self.assertRaisesMessage(FieldError, msg):
            query.build_where(Q(creator__num__gt=2))