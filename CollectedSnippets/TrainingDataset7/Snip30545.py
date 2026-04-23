def test_foreign_key_f(self):
        query = Query(Ranking)
        with self.assertRaises(FieldError):
            query.build_where(Q(rank__gt=F("author__num")))