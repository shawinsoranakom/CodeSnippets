def test_ticket7045(self):
        # Extra tables used to crash SQL construction on the second use.
        qs = Ranking.objects.extra(tables=["django_site"])
        qs.query.get_compiler(qs.db).as_sql()
        # test passes if this doesn't raise an exception.
        qs.query.get_compiler(qs.db).as_sql()